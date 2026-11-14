package com.conduit.backendgateway.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.inOrder;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.conduit.backendgateway.domain.KnowledgeBase;
import com.conduit.backendgateway.domain.enums.KbStatus;
import com.conduit.backendgateway.rag.AiServiceClient;
import com.conduit.backendgateway.rag.ChunkEmbeddingResult;
import com.conduit.backendgateway.repository.KnowledgeBaseRepository;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InOrder;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

/** TASK-57a: buoc chay nen. Moi loi phai dua file ve failed va khong ghi doan nao. */
class KnowledgeBaseIngestionServiceTest {

    private final KnowledgeBaseRepository repository = mock(KnowledgeBaseRepository.class);
    private final AiServiceClient aiServiceClient = mock(AiServiceClient.class);
    private final PlatformTransactionManager transactionManager = mock(PlatformTransactionManager.class);
    private final UUID kbId = UUID.randomUUID();
    private final KnowledgeBase kb = new KnowledgeBase();

    private KnowledgeBaseIngestionService service;

    @BeforeEach
    void setUp() {
        service = new KnowledgeBaseIngestionService(repository, aiServiceClient,
                new TransactionTemplate(transactionManager));
        kb.setId(kbId);
        kb.setStatus(KbStatus.processing);
        when(repository.findById(kbId)).thenReturn(Optional.of(kb));
        when(repository.insertChunk(any(), anyString(), anyInt(), anyString())).thenReturn(1);
    }

    private static List<Double> vector(double value) {
        return Collections.nCopies(KnowledgeBaseIngestionService.EMBEDDING_DIMENSIONS, value);
    }

    @Test
    void chunksAreWrittenInOrderThenFileBecomesReady() {
        when(aiServiceClient.chunkAndEmbed("a.txt", new byte[] {1})).thenReturn(new ChunkEmbeddingResult(
                "text-embedding-3-small", 12, List.of(
                        new ChunkEmbeddingResult.Chunk(0, "doan mot", vector(0.25)),
                        new ChunkEmbeddingResult.Chunk(1, "doan hai", vector(-0.5)))));

        service.process(kbId, "a.txt", new byte[] {1});

        InOrder order = inOrder(repository);
        order.verify(repository).insertChunk(eq(kbId), eq("doan mot"), eq(0), eq(literal(0.25)));
        order.verify(repository).insertChunk(eq(kbId), eq("doan hai"), eq(1), eq(literal(-0.5)));
        order.verify(repository).save(kb);
        assertThat(kb.getStatus()).isEqualTo(KbStatus.ready);
    }

    @Test
    void aiServiceFailureMarksFileFailedWithoutWritingChunks() {
        when(aiServiceClient.chunkAndEmbed(anyString(), any())).thenThrow(new IllegalStateException("502"));

        service.process(kbId, "a.txt", new byte[] {1});

        verify(repository, never()).insertChunk(any(), anyString(), anyInt(), anyString());
        assertThat(kb.getStatus()).isEqualTo(KbStatus.failed);
    }

    @Test
    void wrongDimensionOrEmptyResultIsRejectedBeforeWriting() {
        for (ChunkEmbeddingResult bad : List.of(
                new ChunkEmbeddingResult("m", 1, List.of(new ChunkEmbeddingResult.Chunk(0, "x", List.of(0.1, 0.2)))),
                new ChunkEmbeddingResult("m", 1, List.of(new ChunkEmbeddingResult.Chunk(0, " ", vector(0.1)))),
                new ChunkEmbeddingResult("m", 0, List.of()))) {
            kb.setStatus(KbStatus.processing);
            when(aiServiceClient.chunkAndEmbed(anyString(), any())).thenReturn(bad);

            service.process(kbId, "a.txt", new byte[] {1});

            assertThat(kb.getStatus()).isEqualTo(KbStatus.failed);
        }
        verify(repository, never()).insertChunk(any(), anyString(), anyInt(), anyString());
    }

    @Test
    void failureHalfwayRollsBackTheTransactionAndMarksFailed() {
        when(aiServiceClient.chunkAndEmbed(anyString(), any())).thenReturn(new ChunkEmbeddingResult("m", 1, List.of(
                new ChunkEmbeddingResult.Chunk(0, "a", vector(0.1)),
                new ChunkEmbeddingResult.Chunk(1, "b", vector(0.1)))));
        when(repository.insertChunk(eq(kbId), eq("b"), eq(1), anyString()))
                .thenThrow(new IllegalStateException("db down"));

        service.process(kbId, "a.txt", new byte[] {1});

        verify(transactionManager).rollback(any());
        assertThat(kb.getStatus()).isEqualTo(KbStatus.failed);
    }

    @Test
    void vectorLiteralUsesPgvectorTextFormatAndRejectsNonFiniteValues() {
        assertThat(KnowledgeBaseIngestionService.toVectorLiteral(List.of(0.5, -1.0, 1.0E-4)))
                .isEqualTo("[0.5,-1.0,1.0E-4]");
        assertThatThrownBy(() -> KnowledgeBaseIngestionService.toVectorLiteral(List.of(Double.NaN)))
                .isInstanceOf(IllegalStateException.class);
    }

    private static String literal(double value) {
        return KnowledgeBaseIngestionService.toVectorLiteral(vector(value));
    }
}
