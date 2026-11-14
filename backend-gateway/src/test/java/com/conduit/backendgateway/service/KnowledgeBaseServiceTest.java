package com.conduit.backendgateway.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import com.conduit.backendgateway.domain.Agent;
import com.conduit.backendgateway.domain.KnowledgeBase;
import com.conduit.backendgateway.domain.enums.KbStatus;
import com.conduit.backendgateway.dto.knowledgebase.KnowledgeBaseResponse;
import com.conduit.backendgateway.exception.ForbiddenActionException;
import com.conduit.backendgateway.exception.InvalidKnowledgeFileException;
import com.conduit.backendgateway.exception.ResourceNotFoundException;
import com.conduit.backendgateway.repository.AgentRepository;
import com.conduit.backendgateway.repository.KnowledgeBaseRepository;
import com.conduit.backendgateway.storage.ObjectStorage;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.RejectedExecutionException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.mock.web.MockMultipartFile;

/** TASK-57a: ABAC + kiem tra file khi creator tai tai lieu RAG. Khong goi API that. */
class KnowledgeBaseServiceTest {

    private static final long MAX_BYTES = 100;

    private final AgentRepository agentRepository = mock(AgentRepository.class);
    private final KnowledgeBaseRepository knowledgeBaseRepository = mock(KnowledgeBaseRepository.class);
    private final ObjectStorage objectStorage = mock(ObjectStorage.class);
    private final KnowledgeBaseIngestionService ingestionService = mock(KnowledgeBaseIngestionService.class);
    private final List<Runnable> submitted = new ArrayList<>();

    private final UUID ownerId = UUID.randomUUID();
    private final UUID otherCreatorId = UUID.randomUUID();
    private final UUID agentId = UUID.randomUUID();
    private final UUID savedKbId = UUID.randomUUID();

    private KnowledgeBaseService service;

    @BeforeEach
    void setUp() {
        service = new KnowledgeBaseService(agentRepository, knowledgeBaseRepository, objectStorage,
                ingestionService, submitted::add, MAX_BYTES);
        Agent agent = new Agent();
        agent.setId(agentId);
        agent.setCreatorId(ownerId);
        when(agentRepository.findById(agentId)).thenReturn(Optional.of(agent));
        when(objectStorage.put(anyString(), any(), anyString()))
                .thenAnswer(inv -> "s3://conduit-kb/" + inv.getArgument(0));
        when(knowledgeBaseRepository.save(any(KnowledgeBase.class))).thenAnswer(inv -> {
            KnowledgeBase kb = inv.getArgument(0);
            kb.setId(savedKbId);
            return kb;
        });
    }

    private static MockMultipartFile file(String name, String content) {
        return new MockMultipartFile("file", name, "application/octet-stream",
                content.getBytes(StandardCharsets.UTF_8));
    }

    @Test
    void ownerUploadStoresFileSavesProcessingRowAndQueuesIngestion() {
        KnowledgeBaseResponse response = service.upload(agentId, ownerId, file("Huong dan.txt", "xin chao"));

        ArgumentCaptor<String> key = ArgumentCaptor.forClass(String.class);
        verify(objectStorage).put(key.capture(), eq("xin chao".getBytes(StandardCharsets.UTF_8)),
                eq("text/plain; charset=utf-8"));
        assertThat(key.getValue()).startsWith("agents/" + agentId + "/").endsWith("/Huong_dan.txt");

        assertThat(response.id()).isEqualTo(savedKbId);
        assertThat(response.agentId()).isEqualTo(agentId);
        assertThat(response.fileName()).isEqualTo("Huong dan.txt");
        assertThat(response.fileUrl()).isEqualTo("s3://conduit-kb/" + key.getValue());
        assertThat(response.status()).isEqualTo(KbStatus.processing);

        // Chia doan + embedding chay nen, dung id vua luu.
        assertThat(submitted).hasSize(1);
        verifyNoInteractions(ingestionService);
        submitted.get(0).run();
        verify(ingestionService).process(eq(savedKbId), eq("Huong dan.txt"), any());
    }

    @Test
    void pathSentByBrowserIsStrippedFromFileName() {
        KnowledgeBaseResponse response =
                service.upload(agentId, ownerId, file("C:\\Users\\x\\docs/notes.PDF", "%PDF-1.4"));

        assertThat(response.fileName()).isEqualTo("notes.PDF");
        verify(objectStorage).put(anyString(), any(), eq("application/pdf"));
    }

    @Test
    void anotherCreatorCannotUploadToAgentTheyDoNotOwn() {
        assertThatThrownBy(() -> service.upload(agentId, otherCreatorId, file("a.txt", "x")))
                .isInstanceOf(ForbiddenActionException.class);

        verifyNoInteractions(objectStorage);
        verify(knowledgeBaseRepository, never()).save(any());
        assertThat(submitted).isEmpty();
    }

    @Test
    void anotherCreatorCannotListFilesOfAgentTheyDoNotOwn() {
        assertThatThrownBy(() -> service.list(agentId, otherCreatorId))
                .isInstanceOf(ForbiddenActionException.class);
        verify(knowledgeBaseRepository, never()).findByAgentIdOrderByCreatedAtDesc(any());
    }

    @Test
    void ownerListsFilesOfOwnAgent() {
        KnowledgeBase kb = new KnowledgeBase();
        kb.setId(savedKbId);
        kb.setAgentId(agentId);
        kb.setFileName("a.txt");
        kb.setFileUrl("s3://conduit-kb/a.txt");
        kb.setStatus(KbStatus.ready);
        when(knowledgeBaseRepository.findByAgentIdOrderByCreatedAtDesc(agentId)).thenReturn(List.of(kb));

        assertThat(service.list(agentId, ownerId))
                .extracting(KnowledgeBaseResponse::id, KnowledgeBaseResponse::status)
                .containsExactly(org.assertj.core.groups.Tuple.tuple(savedKbId, KbStatus.ready));
    }

    @Test
    void unknownAgentIsNotFound() {
        UUID unknown = UUID.randomUUID();
        when(agentRepository.findById(unknown)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.upload(unknown, ownerId, file("a.txt", "x")))
                .isInstanceOf(ResourceNotFoundException.class);
    }

    @Test
    void invalidFilesAreRejectedBeforeAnythingIsStored() {
        for (MockMultipartFile bad : List.of(
                file("a.docx", "x"),
                file("noextension", "x"),
                file("", "x"),
                file("empty.txt", ""),
                file("big.txt", "x".repeat((int) MAX_BYTES + 1)))) {
            assertThatThrownBy(() -> service.upload(agentId, ownerId, bad))
                    .as(bad.getOriginalFilename())
                    .isInstanceOf(InvalidKnowledgeFileException.class);
        }
        verifyNoInteractions(objectStorage);
        verify(knowledgeBaseRepository, never()).save(any());
    }

    @Test
    void fullIngestionQueueMarksFileFailedInsteadOfLeavingItProcessing() {
        service = new KnowledgeBaseService(agentRepository, knowledgeBaseRepository, objectStorage,
                ingestionService, task -> {
                    throw new RejectedExecutionException("full");
                }, MAX_BYTES);

        KnowledgeBaseResponse response = service.upload(agentId, ownerId, file("a.txt", "x"));

        assertThat(response.status()).isEqualTo(KbStatus.failed);
        verify(ingestionService).markFailed(savedKbId);
    }
}
