package com.travelmate.domain.expense.dto;

import com.travelmate.common.enums.ExpenseCategory;
import com.travelmate.domain.expense.entity.Expense;
import com.travelmate.domain.expense.entity.ExpenseSplit;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

public record ExpenseResponse(
        Long id,
        String name,
        BigDecimal amount,
        ExpenseCategory category,
        LocalDate expenseDate,
        PaidByInfo paidBy,
        String note,
        List<SplitInfo> splits,
        LocalDateTime createdAt
) {
    public record PaidByInfo(Long id, String fullName, String avatarUrl) {}
    public record SplitInfo(Long userId, String fullName, BigDecimal amount, boolean isSettled) {}

    public static ExpenseResponse from(Expense e) {
        List<SplitInfo> splits = e.getSplits().stream()
                .map(s -> new SplitInfo(
                        s.getUser().getId(), s.getUser().getFullName(),
                        s.getAmount(), Boolean.TRUE.equals(s.getIsSettled())))
                .toList();
        return new ExpenseResponse(
                e.getId(), e.getName(), e.getAmount(), e.getCategory(),
                e.getExpenseDate(),
                new PaidByInfo(e.getPaidBy().getId(), e.getPaidBy().getFullName(), e.getPaidBy().getAvatarUrl()),
                e.getNote(), splits, e.getCreatedAt());
    }
}
