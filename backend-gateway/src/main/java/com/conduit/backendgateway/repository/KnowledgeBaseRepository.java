package com.conduit.backendgateway.repository;

import com.conduit.backendgateway.domain.KnowledgeBase;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface KnowledgeBaseRepository extends JpaRepository<KnowledgeBase, UUID> {

    List<KnowledgeBase> findByAgentIdOrderByCreatedAtDesc(UUID agentId);

    // kb_chunks chua co entity: cot vector(1536) can kieu rieng cua Hibernate (hibernate-vector),
    // khong dang them dependency chi de ghi. Dung native query co @Param (CLAUDE.md muc 7); vector
    // truyen dang chuoi pgvector '[x,y,...]' roi CAST.
    // agent_id KHONG nhan tu ben goi ma lay tu chinh dong knowledge_bases: doan luon mang dung
    // agent cua file (tenant isolation, CLAUDE.md muc 7).
    @Modifying
    @Query(
            value = "INSERT INTO kb_chunks"
                    + " (knowledge_base_id, agent_id, chunk_text, chunk_index, embedding, source_file)"
                    + " SELECT kb.id, kb.agent_id, :chunkText, :chunkIndex, CAST(:embedding AS vector),"
                    + " kb.file_name FROM knowledge_bases kb WHERE kb.id = :knowledgeBaseId",
            nativeQuery = true)
    int insertChunk(
            @Param("knowledgeBaseId") UUID knowledgeBaseId,
            @Param("chunkText") String chunkText,
            @Param("chunkIndex") int chunkIndex,
            @Param("embedding") String embedding);

    @Query(value = "SELECT count(*) FROM kb_chunks WHERE knowledge_base_id = :knowledgeBaseId",
            nativeQuery = true)
    long countChunks(@Param("knowledgeBaseId") UUID knowledgeBaseId);
}
