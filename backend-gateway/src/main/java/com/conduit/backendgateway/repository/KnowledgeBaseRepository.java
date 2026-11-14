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

    // TASK-57b: agent co tai lieu san sang khong. Khong co thi chat KHONG goi embedding (khong ton
    // phi, request y het luc do thuc nghiem).
    @Query(value = "SELECT EXISTS (SELECT 1 FROM kb_chunks c JOIN knowledge_bases kb"
            + " ON kb.id = c.knowledge_base_id WHERE c.agent_id = :agentId AND kb.status = 'ready')",
            nativeQuery = true)
    boolean hasReadyChunks(@Param("agentId") UUID agentId);

    // TASK-57b: top-k doan gan cau hoi nhat (khoang cach cosine, toan tu <=> cua pgvector).
    // Loc CUNG theo agent_id (tenant isolation, CLAUDE.md muc 7) - agentId lay tu hoi thoai phia
    // server, khong bao gio tu noi dung nguoi dung gui.
    @Query(value = "SELECT c.chunk_text AS chunkText, c.source_file AS sourceFile,"
            + " c.chunk_index AS chunkIndex, (c.embedding <=> CAST(:queryEmbedding AS vector)) AS distance"
            + " FROM kb_chunks c JOIN knowledge_bases kb ON kb.id = c.knowledge_base_id"
            + " WHERE c.agent_id = :agentId AND kb.status = 'ready'"
            + " ORDER BY c.embedding <=> CAST(:queryEmbedding AS vector)"
            + " LIMIT :limit",
            nativeQuery = true)
    List<RetrievedChunk> findNearestChunks(
            @Param("agentId") UUID agentId,
            @Param("queryEmbedding") String queryEmbedding,
            @Param("limit") int limit);

    interface RetrievedChunk {
        String getChunkText();

        String getSourceFile();

        Integer getChunkIndex();

        Double getDistance();
    }
}
