package com.conduit.backendgateway.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.conduit.backendgateway.domain.Agent;
import com.conduit.backendgateway.domain.KnowledgeBase;
import com.conduit.backendgateway.domain.User;
import com.conduit.backendgateway.domain.enums.KbStatus;
import com.conduit.backendgateway.rag.ChunkEmbeddingResult;
import com.conduit.backendgateway.repository.AgentRepository;
import com.conduit.backendgateway.repository.KnowledgeBaseRepository;
import com.conduit.backendgateway.repository.UserRepository;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.transaction.support.TransactionTemplate;

/**
 * TASK-57a "dat khi": nap 1 file -> cac doan nam trong kb_chunks DUNG agent_id.
 *
 * Can DB THAT (pgvector): kiem cau INSERT native + CAST(... AS vector) va cot agent_id lay tu dong
 * knowledge_bases. ai-service duoc thay bang ket qua gia - KHONG goi embedding co phi.
 */
@SpringBootTest
class KnowledgeBaseChunkPersistenceTest {

    @Autowired
    private UserRepository userRepository;
    @Autowired
    private AgentRepository agentRepository;
    @Autowired
    private KnowledgeBaseRepository knowledgeBaseRepository;
    @Autowired
    private TransactionTemplate transactionTemplate;
    @Autowired
    private JdbcTemplate jdbc;

    private final List<UUID> users = new ArrayList<>();
    private final List<UUID> agents = new ArrayList<>();

    @AfterEach
    void cleanUp() {
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
    void chunksAreStoredAsVectorsUnderTheFilesOwnAgent() {
        UUID agentA = newAgent("A");
        UUID agentB = newAgent("B");
        UUID kbA = newKnowledgeBase(agentA, "a.txt");

        ingestionWithFakeEmbeddings(List.of("doan mot cua A", "doan hai cua A", "doan ba cua A"))
                .process(kbA, "a.txt", new byte[] {1});

        assertThat(knowledgeBaseRepository.findById(kbA).orElseThrow().getStatus()).isEqualTo(KbStatus.ready);
        assertThat(knowledgeBaseRepository.countChunks(kbA)).isEqualTo(3);
        assertThat(jdbc.queryForList(
                "SELECT DISTINCT agent_id FROM kb_chunks WHERE knowledge_base_id = ?", UUID.class, kbA))
                .containsExactly(agentA);
        assertThat(jdbc.queryForList(
                "SELECT chunk_index FROM kb_chunks WHERE knowledge_base_id = ? ORDER BY chunk_index",
                Integer.class, kbA)).containsExactly(0, 1, 2);
        assertThat(jdbc.queryForObject(
                "SELECT DISTINCT vector_dims(embedding) FROM kb_chunks WHERE knowledge_base_id = ?",
                Integer.class, kbA)).isEqualTo(1536);
        assertThat(jdbc.queryForObject(
                "SELECT DISTINCT source_file FROM kb_chunks WHERE knowledge_base_id = ?", String.class, kbA))
                .isEqualTo("a.txt");
        // Loc theo agent_id cua B khong thay doan nao cua A.
        assertThat(jdbc.queryForObject("SELECT count(*) FROM kb_chunks WHERE agent_id = ?", Long.class, agentB))
                .isZero();
    }

    private KnowledgeBaseIngestionService ingestionWithFakeEmbeddings(List<String> texts) {
        List<ChunkEmbeddingResult.Chunk> chunks = new ArrayList<>();
        for (int i = 0; i < texts.size(); i++) {
            chunks.add(new ChunkEmbeddingResult.Chunk(i, texts.get(i), Collections.nCopies(1536, 0.001 * (i + 1))));
        }
        return new KnowledgeBaseIngestionService(knowledgeBaseRepository,
                (fileName, data) -> new ChunkEmbeddingResult("fake", 0, chunks), transactionTemplate);
    }

    private UUID newAgent(String label) {
        User creator = new User();
        creator.setEmail("kb-test-" + UUID.randomUUID() + "@conduit.test");
        creator.setFullName("KB test creator " + label);
        UUID creatorId = userRepository.saveAndFlush(creator).getId();
        users.add(creatorId);

        Agent agent = new Agent();
        agent.setCreatorId(creatorId);
        agent.setTitle("KB test agent " + label);
        UUID agentId = agentRepository.saveAndFlush(agent).getId();
        agents.add(agentId);
        return agentId;
    }

    private UUID newKnowledgeBase(UUID agentId, String fileName) {
        KnowledgeBase kb = new KnowledgeBase();
        kb.setAgentId(agentId);
        kb.setFileName(fileName);
        kb.setFileUrl("s3://conduit-kb/test/" + fileName);
        return knowledgeBaseRepository.saveAndFlush(kb).getId();
    }
}
