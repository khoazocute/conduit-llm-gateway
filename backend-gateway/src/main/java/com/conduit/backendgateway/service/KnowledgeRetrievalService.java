package com.conduit.backendgateway.service;

import com.conduit.backendgateway.rag.AiServiceClient;
import com.conduit.backendgateway.rag.QueryEmbedding;
import com.conduit.backendgateway.rag.ReferenceContext;
import com.conduit.backendgateway.repository.KnowledgeBaseRepository;
import com.conduit.backendgateway.repository.KnowledgeBaseRepository.RetrievedChunk;
import java.util.List;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/**
 * TASK-57b: truy hoi top-k doan cua DUNG agent cua hoi thoai, tra ve khoi "ngu canh tham khao".
 *
 * - Agent khong co tai lieu ready -> tra null, KHONG goi embedding: agent thuong va agent thi
 *   nghiem gui request y het truoc day, khong ton them phi.
 * - Truy hoi loi (ai-service/LiteLLM/DB) -> ghi log, tra null: chat van chay, chi khong co ngu canh.
 */
@Service
public class KnowledgeRetrievalService {

    private static final Logger log = LoggerFactory.getLogger(KnowledgeRetrievalService.class);

    private final KnowledgeBaseRepository knowledgeBaseRepository;
    private final AiServiceClient aiServiceClient;
    private final int topK;

    public KnowledgeRetrievalService(
            KnowledgeBaseRepository knowledgeBaseRepository,
            AiServiceClient aiServiceClient,
            @Value("${app.rag.top-k:4}") int topK) {
        this.knowledgeBaseRepository = knowledgeBaseRepository;
        this.aiServiceClient = aiServiceClient;
        this.topK = topK;
    }

    public String referenceContextFor(UUID agentId, String question) {
        if (agentId == null || question == null || question.isBlank() || topK <= 0) {
            return null;
        }
        try {
            if (!knowledgeBaseRepository.hasReadyChunks(agentId)) {
                return null;
            }
            QueryEmbedding query = aiServiceClient.embedQuery(question);
            if (query == null || query.embedding() == null
                    || query.embedding().size() != KnowledgeBaseIngestionService.EMBEDDING_DIMENSIONS) {
                throw new IllegalStateException("ai-service returned an invalid query embedding");
            }
            List<RetrievedChunk> chunks = knowledgeBaseRepository.findNearestChunks(
                    agentId, KnowledgeBaseIngestionService.toVectorLiteral(query.embedding()), topK);
            // Chi phi embedding cau hoi hien chi ghi log (giong luc nap tai lieu) - xem log-khoa.
            log.info("RAG retrieval: agent={} chunks={} model={} prompt_tokens={} distances={}",
                    agentId, chunks.size(), query.model(), query.promptTokens(),
                    chunks.stream().map(RetrievedChunk::getDistance).toList());
            return ReferenceContext.format(chunks);
        } catch (RuntimeException e) {
            log.warn("RAG retrieval failed, answering without reference context: agent={}", agentId, e);
            return null;
        }
    }
}
