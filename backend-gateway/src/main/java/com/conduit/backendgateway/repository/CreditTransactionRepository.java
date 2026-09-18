package com.conduit.backendgateway.repository;

import com.conduit.backendgateway.domain.CreditTransaction;
import com.conduit.backendgateway.domain.enums.CreditTxType;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CreditTransactionRepository extends JpaRepository<CreditTransaction, UUID> {

    Page<CreditTransaction> findByWalletId(UUID walletId, Pageable pageable);

    Page<CreditTransaction> findByWalletIdAndType(UUID walletId, CreditTxType type, Pageable pageable);
}
