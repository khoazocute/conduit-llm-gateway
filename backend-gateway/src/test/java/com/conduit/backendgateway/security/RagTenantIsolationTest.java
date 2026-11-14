package com.conduit.backendgateway.security;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.conduit.backendgateway.adapter.ChatTurn;
import com.conduit.backendgateway.adapter.ProxyChatClient;
import com.conduit.backendgateway.adapter.ProxyChatException;
import com.conduit.backendgateway.domain.Agent;
import com.conduit.backendgateway.domain.Conversation;
import com.conduit.backendgateway.domain.KnowledgeBase;
import com.conduit.backendgateway.domain.User;
import com.conduit.backendgateway.domain.enums.UserRole;
import com.conduit.backendgateway.rag.AiServiceClient;
import com.conduit.backendgateway.rag.ChunkEmbeddingResult;
import com.conduit.backendgateway.rag.QueryEmbedding;
import com.conduit.backendgateway.repository.AgentRepository;
import com.conduit.backendgateway.repository.ConversationRepository;
import com.conduit.backendgateway.repository.KnowledgeBaseRepository;
import com.conduit.backendgateway.repository.UserRepository;
import com.conduit.backendgateway.service.ChatService;
import com.conduit.backendgateway.service.KnowledgeBaseIngestionService;
import com.conduit.backendgateway.storage.ObjectStorage;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

/**
 * TASK-58, test bao mat 1/2 - TENANT ISOLATION (CLAUDE.md muc 7: "creator A khong truy hoi duoc
 * kb_chunks cua B").
 *
 * Chay qua HTTP that (JWT + Spring Security + ABAC) va DB that (pgvector). Chi thay 3 diem goi ra
 * ngoai: ai-service (embedding), kho S3, proxy LLM -> KHONG ton phi.
 *
 * Kich ban: A va B la hai creator, moi nguoi mot agent co tai lieu. Doan cua A chua mot "bi mat".
 * Cau hoi chat voi agent cua B duoc gia lap co embedding TRUNG HUONG doan bi mat cua A (truong hop
 * xau nhat: neu khong loc theo agent, doan cua A se dung top 1).
 */
@SpringBootTest
@AutoConfigureMockMvc
class RagTenantIsolationTest {

    private static final String SECRET_OF_A = "BI_MAT_CUA_A: ma giam gia noi bo la KHOA-2026";
    private static final String DOC_OF_B = "Tai lieu cua B: gio mo cua 9h-18h";

    @Autowired
    private MockMvc mockMvc;
    @Autowired
    private JwtService jwtService;
    @Autowired
    private UserRepository userRepository;
    @Autowired
    private AgentRepository agentRepository;
    @Autowired
    private ConversationRepository conversationRepository;
    @Autowired
    private KnowledgeBaseRepository knowledgeBaseRepository;
    @Autowired
    private KnowledgeBaseIngestionService ingestionService;
    @Autowired
    private ChatService chatService;
    @Autowired
    private JdbcTemplate jdbc;

    @MockitoBean
    private AiServiceClient aiServiceClient;
    @MockitoBean
    private ObjectStorage objectStorage;
    @MockitoBean
    private ProxyChatClient proxyChatClient;

    private final List<UUID> users = new ArrayList<>();
    private final List<UUID> agents = new ArrayList<>();
    private final List<UUID> conversations = new ArrayList<>();

    private User creatorA;
    private User creatorB;
    private UUID agentA;
    private UUID agentB;

    @BeforeEach
    void twoCreatorsEachWithADocument() {
        creatorA = newCreator("A");
        creatorB = newCreator("B");
        agentA = newAgent(creatorA, "A");
        agentB = newAgent(creatorB, "B");
        ingest(agentA, "a-secret.txt", SECRET_OF_A, axis(1));
        ingest(agentB, "b.txt", DOC_OF_B, axis(7));
    }

    @AfterEach
    void cleanUp() {
        for (UUID conversationId : conversations) {
            String messages = "SELECT id FROM messages WHERE conversation_id = ?";
            jdbc.update("DELETE FROM routing_decisions WHERE message_id IN (" + messages + ")", conversationId);
            jdbc.update("DELETE FROM usage_logs WHERE message_id IN (" + messages + ")", conversationId);
            jdbc.update("DELETE FROM credit_transactions WHERE related_message_id IN (" + messages + ")",
                    conversationId);
            jdbc.update("DELETE FROM messages WHERE conversation_id = ?", conversationId);
            jdbc.update("DELETE FROM conversations WHERE id = ?", conversationId);
        }
        for (UUID agentId : agents) {
            jdbc.update("DELETE FROM kb_chunks WHERE agent_id = ?", agentId);
            jdbc.update("DELETE FROM knowledge_bases WHERE agent_id = ?", agentId);
            jdbc.update("DELETE FROM agents WHERE id = ?", agentId);
        }
        for (UUID userId : users) {
            jdbc.update("DELETE FROM users WHERE id = ?", userId);
        }
    }

    @Test
    void creatorBCannotListOrUploadDocumentsOfCreatorAsAgent() throws Exception {
        String tokenA = "Bearer " + jwtService.generateAccessToken(creatorA);
        String tokenB = "Bearer " + jwtService.generateAccessToken(creatorB);
        MockMultipartFile file = new MockMultipartFile("file", "x.txt", "text/plain", "x".getBytes());

        // B xem danh sach tai lieu cua agent A -> 403; chua dang nhap -> 401.
        mockMvc.perform(get("/agents/{id}/knowledge-base", agentA).header("Authorization", tokenB))
                .andExpect(status().isForbidden());
        mockMvc.perform(get("/agents/{id}/knowledge-base", agentA))
                .andExpect(status().isUnauthorized());
        // B tai file vao agent A -> 403, va khong co gi duoc luu.
        mockMvc.perform(multipart("/agents/{id}/knowledge-base", agentA).file(file).header("Authorization", tokenB))
                .andExpect(status().isForbidden());
        verifyNoInteractions(objectStorage);
        assertThat(knowledgeBaseRepository.findByAgentIdOrderByCreatedAtDesc(agentA)).hasSize(1);

        // Chu agent thi xem duoc, va chi thay file cua chinh agent do.
        mockMvc.perform(get("/agents/{id}/knowledge-base", agentA).header("Authorization", tokenA))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(1))
                .andExpect(jsonPath("$[0].file_name").value("a-secret.txt"))
                .andExpect(jsonPath("$[0].agent_id").value(agentA.toString()));
    }

    @Test
    @SuppressWarnings("unchecked")
    void chatWithAgentBNeverRetrievesChunksOfAgentAEvenWhenTheQuestionMatchesThemBest() {
        // Hoi thoai cua creator B voi agent cua B.
        Conversation conversation = new Conversation();
        conversation.setUserId(creatorB.getId());
        conversation.setAgentId(agentB);
        UUID conversationId = conversationRepository.saveAndFlush(conversation).getId();
        conversations.add(conversationId);

        // Embedding cau hoi TRUNG HUONG doan bi mat cua A (axis 1), xa doan cua B (axis 7).
        when(aiServiceClient.embedQuery(anyString()))
                .thenReturn(new QueryEmbedding("fake", 1, axis(1)));
        // Proxy gia: chi can bat lai prompt gui di, roi bao loi de khong phai di qua buoc tru credit.
        when(proxyChatClient.complete(anyString(), any())).thenThrow(new ProxyChatException("stop here", null));

        chatService.sendMessage(conversationId, creatorB.getId(),
                "Cho toi ma giam gia noi bo trong tai lieu", new SseEmitter());

        ArgumentCaptor<List<ChatTurn>> turns = ArgumentCaptor.forClass(List.class);
        verify(proxyChatClient).complete(anyString(), turns.capture());
        String prompt = turns.getValue().toString();
        assertThat(prompt).as("ngu canh cua chinh agent B duoc dua vao").contains(DOC_OF_B);
        assertThat(prompt).as("doan cua agent A KHONG BAO GIO lot vao hoi thoai voi agent B")
                .doesNotContain("BI_MAT_CUA_A").doesNotContain("KHOA-2026").doesNotContain("a-secret.txt");
        verify(aiServiceClient).embedQuery(eq("Cho toi ma giam gia noi bo trong tai lieu"));
    }

    // ------------------------------------------------------------------ helpers

    private User newCreator(String label) {
        User user = new User();
        user.setEmail("rag-sec-" + label + "-" + UUID.randomUUID() + "@conduit.test");
        user.setFullName("RAG security creator " + label);
        user.setRole(UserRole.creator);
        user = userRepository.saveAndFlush(user);
        users.add(user.getId());
        return user;
    }

    private UUID newAgent(User creator, String label) {
        Agent agent = new Agent();
        agent.setCreatorId(creator.getId());
        agent.setTitle("RAG security agent " + label);
        UUID id = agentRepository.saveAndFlush(agent).getId();
        agents.add(id);
        return id;
    }

    // Nap tai lieu qua dung duong that (KnowledgeBaseIngestionService -> INSERT native), chi gia ket
    // qua embedding cua ai-service.
    private void ingest(UUID agentId, String fileName, String text, List<Double> embedding) {
        KnowledgeBase kb = new KnowledgeBase();
        kb.setAgentId(agentId);
        kb.setFileName(fileName);
        kb.setFileUrl("s3://conduit-kb/test/" + fileName);
        UUID kbId = knowledgeBaseRepository.saveAndFlush(kb).getId();
        when(aiServiceClient.chunkAndEmbed(eq(fileName), any())).thenReturn(new ChunkEmbeddingResult(
                "fake", 1, List.of(new ChunkEmbeddingResult.Chunk(0, text, embedding))));
        ingestionService.process(kbId, fileName, new byte[] {1});
        assertThat(knowledgeBaseRepository.countChunks(kbId)).isEqualTo(1);
    }

    private static List<Double> axis(int dimension) {
        List<Double> v = new ArrayList<>(Collections.nCopies(1536, 0.0));
        v.set(dimension, 1.0);
        return v;
    }
}
