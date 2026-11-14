package com.conduit.backendgateway.exception;

// File kien thuc (RAG) khong hop le: sai dinh dang, rong, qua lon -> 400.
public class InvalidKnowledgeFileException extends RuntimeException {
    public InvalidKnowledgeFileException(String message) {
        super(message);
    }
}
