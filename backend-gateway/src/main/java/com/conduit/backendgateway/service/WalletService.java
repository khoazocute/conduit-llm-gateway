package com.conduit.backendgateway.service;

import com.conduit.backendgateway.domain.enums.CreditTxType;
import com.conduit.backendgateway.dto.wallet.CreditTransactionListResponse;
import com.conduit.backendgateway.dto.wallet.CreditWalletResponse;
import com.conduit.backendgateway.repository.CreditTransactionRepository;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

@Service
public class WalletService {

    private final CreditService creditService;
    private final CreditTransactionRepository creditTransactionRepository;

    public WalletService(CreditService creditService, CreditTransactionRepository creditTransactionRepository) {
        this.creditService = creditService;
        this.creditTransactionRepository = creditTransactionRepository;
    }

    public CreditWalletResponse getWallet(UUID userId) {
        return CreditWalletResponse.from(creditService.getWalletOrThrow(userId));
    }

    public CreditTransactionListResponse listTransactions(UUID userId, CreditTxType type, Pageable pageable) {
        var wallet = creditService.getWalletOrThrow(userId);
        Page<com.conduit.backendgateway.domain.CreditTransaction> page = type == null
                ? creditTransactionRepository.findByWalletId(wallet.getId(), pageable)
                : creditTransactionRepository.findByWalletIdAndType(wallet.getId(), type, pageable);
        return CreditTransactionListResponse.from(page);
    }
}
