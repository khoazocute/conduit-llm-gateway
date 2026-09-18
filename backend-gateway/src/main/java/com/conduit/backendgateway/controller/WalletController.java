package com.conduit.backendgateway.controller;

import com.conduit.backendgateway.domain.enums.CreditTxType;
import com.conduit.backendgateway.dto.wallet.CreditTransactionListResponse;
import com.conduit.backendgateway.dto.wallet.CreditWalletResponse;
import com.conduit.backendgateway.security.UserPrincipal;
import com.conduit.backendgateway.service.WalletService;
import org.springframework.data.domain.PageRequest;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/wallet")
public class WalletController {

    private final WalletService walletService;

    public WalletController(WalletService walletService) {
        this.walletService = walletService;
    }

    @GetMapping
    public CreditWalletResponse getWallet(@AuthenticationPrincipal UserPrincipal principal) {
        return walletService.getWallet(principal.getId());
    }

    @GetMapping("/transactions")
    public CreditTransactionListResponse listTransactions(
            @AuthenticationPrincipal UserPrincipal principal,
            @RequestParam(required = false) CreditTxType type,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return walletService.listTransactions(principal.getId(), type, PageRequest.of(page, size));
    }
}
