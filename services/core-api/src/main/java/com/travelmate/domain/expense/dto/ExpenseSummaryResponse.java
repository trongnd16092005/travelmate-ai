package com.travelmate.domain.expense.dto;

import com.travelmate.common.enums.ExpenseCategory;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

public record ExpenseSummaryResponse(
        BigDecimal totalExpense,
        BigDecimal budget,
        Double budgetUsedPercent,
        Map<ExpenseCategory, BigDecimal> byCategory,
        List<ExpenseResponse> recentExpenses
) {}
