package com.conduit.backendgateway.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.conduit.backendgateway.domain.User;
import com.conduit.backendgateway.domain.enums.CreditTxType;
import com.conduit.backendgateway.exception.InsufficientCreditException;
import com.conduit.backendgateway.repository.UserRepository;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.orm.ObjectOptimisticLockingFailureException;

/**
 * TASK-54 (CLAUDE.md muc 4): tru credit dong thoi khong duoc lam so du am, khong duoc tru hut.
 *
 * Can DB THAT: khoa lac quan (@Version o CreditWallet) chi co tac dung khi nhieu transaction that
 * cung UPDATE mot dong - mock khong tai hien duoc. Vi vay test KHONG gan @Transactional: moi lan
 * tru phai la mot transaction rieng, commit that, nhu luc chay that.
 *
 * Bat bien kiem tra: so du cuoi = so du dau - tong so tien cua cac giao dich DA GHI. Neu bo
 * @Version, hai luong cung doc so du cu roi cung ghi de (lost update) -> so du chi giam 1 lan
 * nhung co 2 giao dich -> bat bien vo. Da thu bo @Version: test nay FAIL (xem log-khoa.md).
 */
@SpringBootTest
class CreditServiceConcurrencyTest {

    private static final int THREADS = 24;

    @Autowired
    private CreditService creditService;
    @Autowired
    private UserRepository userRepository;
    @Autowired
    private JdbcTemplate jdbc;

    private UUID userId;
    private UUID walletId;

    @BeforeEach
    void createUserWithWallet() {
        User user = new User();
        user.setEmail("concurrency-test-" + UUID.randomUUID() + "@conduit.test");
        user.setFullName("Concurrency test");
        userId = userRepository.saveAndFlush(user).getId();

        // Tao vi bang SQL (DB tu dien version = 0) thay vi qua entity: nho vay khi bo @Version de
        // kiem chung test, chi co CO CHE KHOA bi tat - khong phai buoc tao vi hong vi version null.
        walletId = UUID.randomUUID();
        jdbc.update("INSERT INTO credit_wallets (id, user_id, balance, updated_at) VALUES (?, ?, 0, now())",
                walletId, userId);
    }

    @AfterEach
    void cleanUp() {
        jdbc.update("DELETE FROM credit_transactions WHERE wallet_id = ?", walletId);
        jdbc.update("DELETE FROM credit_wallets WHERE id = ?", walletId);
        jdbc.update("DELETE FROM users WHERE id = ?", userId);
    }

    @Test
    void concurrentDebitsWithEnoughBalanceNeverLoseAnUpdate() throws Exception {
        setBalance(1_000);

        Outcome outcome = debitConcurrently(THREADS, 7);

        assertThat(outcome.unexpected).as("chi duoc thua khoa lac quan, khong loi nao khac").isEmpty();
        assertThat(outcome.succeeded.get()).as("phai co luot thanh cong").isPositive();
        assertBalanceMatchesLedger(1_000);
        assertThat(balance()).isEqualTo(1_000 - 7L * outcome.succeeded.get());
    }

    @Test
    void concurrentDebitsBeyondBalanceNeverGoNegative() throws Exception {
        // 5 credit, 24 luong cung tru 1: toi da 5 luot duoc phep thanh cong.
        setBalance(5);

        Outcome outcome = debitConcurrently(THREADS, 1);

        assertThat(outcome.unexpected).as("chi duoc thua khoa lac quan hoac het credit").isEmpty();
        assertThat(balance()).as("so du khong bao gio am").isGreaterThanOrEqualTo(0);
        assertThat(outcome.succeeded.get()).isLessThanOrEqualTo(5);
        assertBalanceMatchesLedger(5);
    }

    // ------------------------------------------------------------------ helpers

    private record Outcome(AtomicInteger succeeded, AtomicInteger rejected, List<Throwable> unexpected) {
    }

    private Outcome debitConcurrently(int threads, long amount) throws Exception {
        AtomicInteger succeeded = new AtomicInteger();
        AtomicInteger rejected = new AtomicInteger();
        List<Throwable> unexpected = java.util.Collections.synchronizedList(new ArrayList<>());
        CountDownLatch ready = new CountDownLatch(threads);
        CountDownLatch go = new CountDownLatch(1);

        ExecutorService pool = Executors.newFixedThreadPool(threads);
        try {
            List<Future<?>> futures = new ArrayList<>();
            for (int i = 0; i < threads; i++) {
                futures.add(pool.submit(() -> {
                    ready.countDown();
                    try {
                        go.await(); // tat ca cung xuat phat de toi da hoa tranh chap
                        creditService.debit(userId, amount, CreditTxType.usage_deduct, null, null,
                                "concurrency test");
                        succeeded.incrementAndGet();
                    } catch (ObjectOptimisticLockingFailureException | InsufficientCreditException e) {
                        rejected.incrementAndGet(); // tu choi sach: khong tru, khong ghi giao dich
                    } catch (Throwable t) {
                        unexpected.add(t);
                    }
                    return null;
                }));
            }
            ready.await(10, TimeUnit.SECONDS);
            go.countDown();
            for (Future<?> f : futures) {
                f.get(60, TimeUnit.SECONDS);
            }
        } finally {
            pool.shutdownNow();
        }
        assertThat(succeeded.get() + rejected.get() + unexpected.size()).isEqualTo(threads);
        return new Outcome(succeeded, rejected, unexpected);
    }

    private void setBalance(long amount) {
        jdbc.update("UPDATE credit_wallets SET balance = ? WHERE id = ?", amount, walletId);
    }

    private long balance() {
        return jdbc.queryForObject("SELECT balance FROM credit_wallets WHERE id = ?", Long.class, walletId);
    }

    /** So du cuoi phai bang so du dau cong tong cac giao dich da ghi (amount am = tru). */
    private void assertBalanceMatchesLedger(long startingBalance) {
        Long ledger = jdbc.queryForObject(
                "SELECT COALESCE(SUM(amount), 0) FROM credit_transactions WHERE wallet_id = ?",
                Long.class, walletId);
        assertThat(balance())
                .as("so du phai khop so cai: khong co luot nao bi ghi de (lost update)")
                .isEqualTo(startingBalance + ledger);
    }
}
