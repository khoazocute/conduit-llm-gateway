package com.conduit.backendgateway.service;

import com.conduit.backendgateway.domain.KnowledgeBase;
import com.conduit.backendgateway.domain.enums.KbStatus;
import com.conduit.backendgateway.rag.AiServiceClient;
import com.conduit.backendgateway.rag.ChunkEmbeddingResult;
import com.conduit.backendgateway.repository.KnowledgeBaseRepository;
import java.util.List;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;

// TASK-57a, buoc chay nen sau khi upload: goi ai-service (chia doan + embedding) roi ghi kb_chunks.
// Moi loi deu dua file ve trang thai failed, khong de treo o processing.
@Service
public class KnowledgeBaseIngestionService {

    // kb_chunks.embedding la vector(1536) - text-embedding-3-small.
    static final int EMBEDDING_DIMENSIONS = 1536;

    private static final Logger log = LoggerFactory.getLogger(KnowledgeBaseIngestionService.class);

    private final KnowledgeBaseRepository knowledgeBaseRepository;
    private final AiServiceClient aiServiceClient;
    private final TransactionTemplate transactionTemplate;

    public KnowledgeBaseIngestionService(
            KnowledgeBaseRepository knowledgeBaseRepository,
            AiServiceClient aiServiceClient,
            TransactionTemplate transactionTemplate) {
        this.knowledgeBaseRepository = knowledgeBaseRepository;
        this.aiServiceClient = aiServiceClient;
        this.transactionTemplate = transactionTemplate;
    }

    public void process(UUID knowledgeBaseId, String fileName, byte[] data) {
        try {
            ChunkEmbeddingResult result = aiServiceClient.chunkAndEmbed(fileName, data);
            List<ChunkEmbeddingResult.Chunk> chunks = validate(result);
            // Ghi het cac doan va doi trang thai trong MOT transaction: hoac du doan + ready,
            // hoac khong co doan nao.
            transactionTemplate.executeWithoutResult(status -> {
                for (ChunkEmbeddingResult.Chunk chunk : chunks) {
                    int inserted = knowledgeBaseRepository.insertChunk(
                            knowledgeBaseId, chunk.text(), chunk.index(), toVectorLiteral(chunk.embedding()));
                    if (inserted != 1) {
                        throw new IllegalStateException("Knowledge base row disappeared: " + knowledgeBaseId);
                    }
                }
                setStatus(knowledgeBaseId, KbStatus.ready);
            });
            // Chi phi embedding hien chi ghi log (usage_logs gan voi tin nhan chat) - xem log-khoa.
            log.info("Knowledge base ready: kb={} chunks={} model={} prompt_tokens={}",
                    knowledgeBaseId, chunks.size(), result.model(), result.promptTokens());
        } catch (RuntimeException e) {
            log.warn("Knowledge base ingestion failed: kb={}", knowledgeBaseId, e);
            markFailed(knowledgeBaseId);
        }
    }

    public void markFailed(UUID knowledgeBaseId) {
        try {
            transactionTemplate.executeWithoutResult(status -> setStatus(knowledgeBaseId, KbStatus.failed));
        } catch (RuntimeException e) {
            log.error("Could not mark knowledge base failed: kb={}", knowledgeBaseId, e);
        }
    }

    private void setStatus(UUID knowledgeBaseId, KbStatus status) {
        KnowledgeBase kb = knowledgeBaseRepository.findById(knowledgeBaseId)
                .orElseThrow(() -> new IllegalStateException("Knowledge base not found: " + knowledgeBaseId));
        kb.setStatus(status);
        knowledgeBaseRepository.save(kb);
    }

    private static List<ChunkEmbeddingResult.Chunk> validate(ChunkEmbeddingResult result) {
        if (result == null || result.chunks() == null || result.chunks().isEmpty()) {
            throw new IllegalStateException("ai-service returned no chunks");
        }
        for (ChunkEmbeddingResult.Chunk chunk : result.chunks()) {
            if (chunk.text() == null || chunk.text().isBlank()) {
                throw new IllegalStateException("ai-service returned an empty chunk");
            }
            if (chunk.embedding() == null || chunk.embedding().size() != EMBEDDING_DIMENSIONS) {
                throw new IllegalStateException("Embedding must have " + EMBEDDING_DIMENSIONS + " dimensions");
            }
        }
        return result.chunks();
    }

    // Dang van ban pgvector: [0.1,-0.2,...]
    static String toVectorLiteral(List<Double> embedding) {
        StringBuilder sb = new StringBuilder(embedding.size() * 12).append('[');
        for (int i = 0; i < embedding.size(); i++) {
            Double value = embedding.get(i);
            if (value == null || !Double.isFinite(value)) {
                throw new IllegalStateException("Embedding contains a non-finite value");
            }
            if (i > 0) {
                sb.append(',');
            }
            sb.append(value);
        }
        return sb.append(']').toString();
    }
}
