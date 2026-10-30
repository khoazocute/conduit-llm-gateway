package com.conduit.backendgateway.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.conduit.backendgateway.domain.CreditTransaction;
import com.conduit.backendgateway.domain.CreditWallet;
import com.conduit.backendgateway.domain.enums.CreditTxType;
import com.conduit.backendgateway.exception.InsufficientCreditException;
import com.conduit.backendgateway.exception.ResourceNotFoundException;
import com.conduit.backendgateway.repository.CreditTransactionRepository;
import com.conduit.backendgateway.repository.CreditWalletRepository;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.orm.ObjectOptimisticLockingFailureException;

/**
 * TASK-53: logic cua CreditService voi repository MOCK. Phan tranh chap that (nhieu transaction
 * cung UPDATE) can DB that - xem CreditServiceConcurrencyTest (TASK-54).
 */
class CreditServiceTest {

    private static final UUID USER = UUID.randomUUID();

    private final CreditWalletRepository walletRepository = mock(CreditWalletRepository.class);
    private final CreditTransactionRepository txRepository = mock(CreditTransactionRepository.class);
    private CreditWallet wallet;

    @BeforeEach
    void setUp() {
        wallet = new CreditWallet();
        wallet.setId(UUID.randomUUID());
        wallet.setUserId(USER);
        wallet.setBalance(100L);
        when(walletRepository.findByUserId(USER)).thenReturn(Optional.of(wallet));
        when(txRepository.saveAndFlush(any(CreditTransaction.class))).thenAnswer(inv -> inv.getArgument(0));
    }

    private CreditService service(CreditService self) {
        return new CreditService(walletRepository, txRepository, self);
    }

    @Test
    void debitSubtractsAndRecordsANegativeTransaction() {
        CreditService svc = service(null);

        CreditTransaction tx = svc.doApply(USER, -30, CreditTxType.usage_deduct, null, null, "chat");

        assertThat(wallet.getBalance()).isEqualTo(70L);
        assertThat(tx.getAmount()).isEqualTo(-30L);
        assertThat(tx.getWalletId()).isEqualTo(wallet.getId());
        verify(walletRepository).saveAndFlush(wallet);
    }

    @Test
    void debitBeyondBalanceIsRejectedWithoutTouchingTheWallet() {
        CreditService svc = service(null);

        assertThatThrownBy(() -> svc.doApply(USER, -101, CreditTxType.usage_deduct, null, null, "chat"))
                .isInstanceOf(InsufficientCreditException.class);

        assertThat(wallet.getBalance()).isEqualTo(100L);
        verify(walletRepository, never()).saveAndFlush(any());
        verify(txRepository, never()).saveAndFlush(any());
    }

    @Test
    void debitToExactlyZeroIsAllowed() {
        service(null).doApply(USER, -100, CreditTxType.usage_deduct, null, null, "chat");
        assertThat(wallet.getBalance()).isZero();
    }

    @Test
    void creditAddsAndLinksThePurchase() {
        UUID purchaseId = UUID.randomUUID();
        CreditTransaction tx = service(null).doApply(USER, 500, CreditTxType.purchase_grant, null, purchaseId, "grant");

        assertThat(wallet.getBalance()).isEqualTo(600L);
        assertThat(tx.getRelatedPurchaseId()).isEqualTo(purchaseId);
    }

    @Test
    void missingWalletIsNotFound() {
        when(walletRepository.findByUserId(USER)).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service(null).getWalletOrThrow(USER)).isInstanceOf(ResourceNotFoundException.class);
    }

    @Test
    void debitPassesANegativeAmountThroughTheTransactionalProxy() {
        CreditService self = mock(CreditService.class);
        service(self).debit(USER, 25, CreditTxType.usage_deduct, null, null, "chat");

        ArgumentCaptor<Long> amount = ArgumentCaptor.forClass(Long.class);
        verify(self).doApply(eq(USER), amount.capture(), eq(CreditTxType.usage_deduct), any(), any(), eq("chat"));
        assertThat(amount.getValue()).isEqualTo(-25L);
    }

    @Test
    void optimisticLockConflictIsRetriedThenSucceeds() {
        CreditService self = mock(CreditService.class);
        CreditTransaction ok = new CreditTransaction();
        when(self.doApply(any(), anyLong(), any(), any(), any(), any()))
                .thenThrow(new ObjectOptimisticLockingFailureException(CreditWallet.class, wallet.getId()))
                .thenReturn(ok);

        assertThat(service(self).debit(USER, 1, CreditTxType.usage_deduct, null, null, "chat")).isSameAs(ok);
        verify(self, times(2)).doApply(any(), anyLong(), any(), any(), any(), any());
    }

    @Test
    void optimisticLockConflictGivesUpAfterThreeAttempts() {
        CreditService self = mock(CreditService.class);
        when(self.doApply(any(), anyLong(), any(), any(), any(), any()))
                .thenThrow(new ObjectOptimisticLockingFailureException(CreditWallet.class, wallet.getId()));

        assertThatThrownBy(() -> service(self).debit(USER, 1, CreditTxType.usage_deduct, null, null, "chat"))
                .isInstanceOf(ObjectOptimisticLockingFailureException.class);
        verify(self, times(3)).doApply(any(), anyLong(), any(), any(), any(), any());
    }

    @Test
    void insufficientCreditIsNotRetried() {
        CreditService self = mock(CreditService.class);
        when(self.doApply(any(), anyLong(), any(), any(), any(), any()))
                .thenThrow(new InsufficientCreditException("Not enough credit balance"));

        assertThatThrownBy(() -> service(self).debit(USER, 1, CreditTxType.usage_deduct, null, null, "chat"))
                .isInstanceOf(InsufficientCreditException.class);
        verify(self, times(1)).doApply(any(), anyLong(), any(), any(), any(), any());
    }
}
