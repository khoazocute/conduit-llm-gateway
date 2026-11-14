package com.conduit.backendgateway.service;

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
import jakarta.annotation.PreDestroy;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.Executor;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

// RAG (Should-have) TASK-57a: creator tai file PDF/TXT cho agent CUA MINH -> luu kho S3 ->
// chia doan + embedding chay nen -> kb_chunks. ABAC: chi chu agent tai len va xem duoc.
@Service
public class KnowledgeBaseService {

    private static final Logger log = LoggerFactory.getLogger(KnowledgeBaseService.class);
    private static final int MAX_FILE_NAME_LENGTH = 255;

    private final AgentRepository agentRepository;
    private final KnowledgeBaseRepository knowledgeBaseRepository;
    private final ObjectStorage objectStorage;
    private final KnowledgeBaseIngestionService ingestionService;
    private final Executor executor;
    private final long maxFileBytes;

    // Executor rieng, KHONG khai bao thanh bean: mot bean Executor bat ky co the lam Spring Boot bo
    // applicationTaskExecutor mac dinh. 2 luong, hang doi 20 - du cho vai file nho.
    @Autowired
    public KnowledgeBaseService(
            AgentRepository agentRepository,
            KnowledgeBaseRepository knowledgeBaseRepository,
            ObjectStorage objectStorage,
            KnowledgeBaseIngestionService ingestionService,
            @Value("${app.knowledge-base.max-file-bytes:5242880}") long maxFileBytes) {
        this(agentRepository, knowledgeBaseRepository, objectStorage, ingestionService,
                newIngestionExecutor(), maxFileBytes);
    }

    KnowledgeBaseService(
            AgentRepository agentRepository,
            KnowledgeBaseRepository knowledgeBaseRepository,
            ObjectStorage objectStorage,
            KnowledgeBaseIngestionService ingestionService,
            Executor executor,
            long maxFileBytes) {
        this.agentRepository = agentRepository;
        this.knowledgeBaseRepository = knowledgeBaseRepository;
        this.objectStorage = objectStorage;
        this.ingestionService = ingestionService;
        this.executor = executor;
        this.maxFileBytes = maxFileBytes;
    }

    public KnowledgeBaseResponse upload(UUID agentId, UUID currentUserId, MultipartFile file) {
        requireOwnedAgent(agentId, currentUserId);

        String fileName = cleanFileName(file.getOriginalFilename());
        String extension = extensionOf(fileName);
        if (file.isEmpty()) {
            throw new InvalidKnowledgeFileException("File is empty");
        }
        if (file.getSize() > maxFileBytes) {
            throw new InvalidKnowledgeFileException("File is larger than " + maxFileBytes + " bytes");
        }
        byte[] data;
        try {
            data = file.getBytes();
        } catch (IOException e) {
            throw new UncheckedIOException("Could not read uploaded file", e);
        }

        String key = "agents/" + agentId + "/" + UUID.randomUUID() + "/" + toKeySegment(fileName);
        String contentType = extension.equals(".pdf") ? "application/pdf" : "text/plain; charset=utf-8";
        String fileUrl = objectStorage.put(key, data, contentType);

        KnowledgeBase kb = new KnowledgeBase();
        kb.setAgentId(agentId);
        kb.setFileName(fileName);
        kb.setFileUrl(fileUrl);
        kb.setStatus(KbStatus.processing);
        kb = knowledgeBaseRepository.save(kb);

        UUID knowledgeBaseId = kb.getId();
        try {
            executor.execute(() -> ingestionService.process(knowledgeBaseId, fileName, data));
        } catch (RejectedExecutionException e) {
            log.warn("Ingestion queue full, knowledge base marked failed: kb={}", knowledgeBaseId);
            ingestionService.markFailed(knowledgeBaseId);
            kb.setStatus(KbStatus.failed);
        }
        return KnowledgeBaseResponse.from(kb);
    }

    public List<KnowledgeBaseResponse> list(UUID agentId, UUID currentUserId) {
        requireOwnedAgent(agentId, currentUserId);
        return knowledgeBaseRepository.findByAgentIdOrderByCreatedAtDesc(agentId).stream()
                .map(KnowledgeBaseResponse::from)
                .toList();
    }

    private void requireOwnedAgent(UUID agentId, UUID currentUserId) {
        Agent agent = agentRepository.findById(agentId)
                .orElseThrow(() -> new ResourceNotFoundException("Agent not found"));
        if (!agent.getCreatorId().equals(currentUserId)) {
            throw new ForbiddenActionException("You do not own this agent");
        }
    }

    // Chi giu ten file (bo duong dan trinh duyet co the gui kem), gioi han do dai cot.
    static String cleanFileName(String originalFileName) {
        String name = originalFileName == null ? "" : originalFileName.strip();
        name = name.substring(Math.max(name.lastIndexOf('/'), name.lastIndexOf('\\')) + 1);
        if (name.isEmpty()) {
            throw new InvalidKnowledgeFileException("File name is required");
        }
        if (name.length() > MAX_FILE_NAME_LENGTH) {
            throw new InvalidKnowledgeFileException("File name is too long");
        }
        return name;
    }

    static String extensionOf(String fileName) {
        String lower = fileName.toLowerCase(Locale.ROOT);
        if (lower.endsWith(".pdf")) {
            return ".pdf";
        }
        if (lower.endsWith(".txt")) {
            return ".txt";
        }
        throw new InvalidKnowledgeFileException("Only .pdf and .txt files are supported");
    }

    // Key S3 chi gom ky tu an toan; ten that van luu nguyen o cot file_name.
    static String toKeySegment(String fileName) {
        return fileName.replaceAll("[^A-Za-z0-9._-]", "_");
    }

    private static ExecutorService newIngestionExecutor() {
        AtomicInteger counter = new AtomicInteger();
        return new ThreadPoolExecutor(2, 2, 0, TimeUnit.SECONDS, new ArrayBlockingQueue<>(20), runnable -> {
            Thread thread = new Thread(runnable, "kb-ingest-" + counter.incrementAndGet());
            thread.setDaemon(true);
            return thread;
        });
    }

    @PreDestroy
    void shutdown() {
        if (executor instanceof ExecutorService service) {
            service.shutdown();
        }
    }
}
