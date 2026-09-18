package com.conduit.backendgateway.service;

import com.conduit.backendgateway.domain.CreditTransaction;
import com.conduit.backendgateway.domain.CreditWallet;
import com.conduit.backendgateway.domain.enums.CreditTxType;
import com.conduit.backendgateway.exception.InsufficientCreditException;
import com.conduit.backendgateway.exception.ResourceNotFoundException;
import com.conduit.backendgateway.repository.CreditTransactionRepository;
import com.conduit.backendgateway.repository.CreditWalletRepository;
import java.util.UUID;
import org.springframework.context.annotation.Lazy;
import org.springframework.orm.ObjectOptimisticLockingFailureException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class CreditService {

    private static final int MAX_RETRY = 3;

    private final CreditWalletRepository creditWalletRepository;
    private final CreditTransactionRepository creditTransactionRepository;
    // Self-injection (via a lazy proxy) is required so retries below go through
    // the Spring AOP proxy - a plain `this.doApply(...)` call bypasses the proxy
    // entirely and @Transactional on doApply would silently do nothing.
    private final CreditService self;

    public CreditService(
            CreditWalletRepository creditWalletRepository,
            CreditTransactionRepository creditTransactionRepository,
            @Lazy CreditService self) {
        this.creditWalletRepository = creditWalletRepository;
        this.creditTransactionRepository = creditTransactionRepository;
        this.self = self;
    }

    public CreditWallet getWalletOrThrow(UUID userId) {
        return creditWalletRepository.findByUserId(userId)
                .orElseThrow(() -> new ResourceNotFoundException("Wallet not found"));
    }

    public CreditTransaction credit(UUID userId, long amount, CreditTxType type,
            UUID relatedMessageId, UUID relatedPurchaseId, String description) {
        return applyChange(userId, amount, type, relatedMessageId, relatedPurchaseId, description);
    }

    public CreditTransaction debit(UUID userId, long amount, CreditTxType type,
            UUID relatedMessageId, UUID relatedPurchaseId, String description) {
        return applyChange(userId, -amount, type, relatedMessageId, relatedPurchaseId, description);
    }

    // amount duong = cong, am = tru (dung quy uoc cua credit_transactions.amount)
    private CreditTransaction applyChange(UUID userId, long amount, CreditTxType type,
            UUID relatedMessageId, UUID relatedPurchaseId, String description) {
        for (int attempt = 0; attempt < MAX_RETRY; attempt++) {
            try {
                return self.doApply(userId, amount, type, relatedMessageId, relatedPurchaseId, description);
            } catch (ObjectOptimisticLockingFailureException e) {
                if (attempt == MAX_RETRY - 1) {
                    throw e;
                }
                // thua concurrent update, vong lap se doc lai wallet moi nhat va thu lai
            }
        }
        throw new IllegalStateException("unreachable");
    }

    @Transactional
    public CreditTransaction doApply(UUID userId, long amount, CreditTxType type,
            UUID relatedMessageId, UUID relatedPurchaseId, String description) {
        CreditWallet wallet = getWalletOrThrow(userId);
        long newBalance = wallet.getBalance() + amount;
        if (newBalance < 0) {
            throw new InsufficientCreditException("Not enough credit balance");
        }
        wallet.setBalance(newBalance);
        creditWalletRepository.saveAndFlush(wallet);

        CreditTransaction tx = new CreditTransaction();
        tx.setWalletId(wallet.getId());
        tx.setType(type);
        tx.setAmount(amount);
        tx.setRelatedMessageId(relatedMessageId);
        tx.setRelatedPurchaseId(relatedPurchaseId);
        tx.setDescription(description);
        return creditTransactionRepository.saveAndFlush(tx);
    }
}
