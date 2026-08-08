package com.travelmate.domain.expense.dto;

import com.travelmate.common.enums.ExpenseCategory;
import jakarta.validation.constraints.*;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

public record CreateExpenseRequest(
        @NotBlank(message = "Tên khoản chi không được để trống")
        @Size(max = 255)
        String name,

        @NotNull(message = "Số tiền không được để trống")
        @DecimalMin(value = "0.01", message = "Số tiền phải lớn hơn 0")
        BigDecimal amount,

        @NotNull(message = "Danh mục không được để trống")
        ExpenseCategory category,

        @NotNull(message = "Ngày không được để trống")
        LocalDate expenseDate,

        Long paidByUserId,   // null = current user

        String note,

        @NotNull(message = "Kiểu chia tiền không được để trống")
        SplitType splitType,

        List<Long> splitWithUserIds,              // for EQUAL
        Map<Long, BigDecimal> customSplits        // for CUSTOM (userId -> amount)
) {
    public enum SplitType { EQUAL, CUSTOM, SINGLE }
}
