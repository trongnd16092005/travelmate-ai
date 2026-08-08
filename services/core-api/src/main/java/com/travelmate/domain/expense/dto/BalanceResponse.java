package com.travelmate.domain.expense.dto;

import java.math.BigDecimal;
import java.util.List;

public record BalanceResponse(
        BigDecimal totalExpense,
        BigDecimal budget,
        Double budgetUsedPercent,
        List<DebtInfo> balances
) {
    public record DebtInfo(
            UserInfo from,
            UserInfo to,
            BigDecimal amount
    ) {}

    public record UserInfo(Long id, String fullName) {}
}
