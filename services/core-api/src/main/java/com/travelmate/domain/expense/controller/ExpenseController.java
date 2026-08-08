package com.travelmate.domain.expense.controller;

import com.travelmate.common.response.ApiResponse;
import com.travelmate.domain.expense.dto.*;
import com.travelmate.domain.expense.service.ExpenseService;
import com.travelmate.security.SecurityUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/trips/{tripId}/expenses")
@RequiredArgsConstructor
@Tag(name = "Expenses", description = "API quản lý chi phí nhóm")
@SecurityRequirement(name = "bearerAuth")
public class ExpenseController {

    private final ExpenseService expenseService;
    private final SecurityUtils securityUtils;

    @GetMapping
    @Operation(summary = "Danh sách chi phí")
    public ResponseEntity<ApiResponse<List<ExpenseResponse>>> getExpenses(@PathVariable Long tripId) {
        return ResponseEntity.ok(ApiResponse.success(
                expenseService.getExpenses(tripId, securityUtils.getCurrentUser())));
    }

    @PostMapping
    @Operation(summary = "Thêm chi phí")
    public ResponseEntity<ApiResponse<ExpenseResponse>> createExpense(
            @PathVariable Long tripId, @Valid @RequestBody CreateExpenseRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.success(
                expenseService.createExpense(tripId, securityUtils.getCurrentUser(), request),
                "Đã thêm chi phí"));
    }

    @PutMapping("/{expenseId}")
    @Operation(summary = "Cập nhật chi phí")
    public ResponseEntity<ApiResponse<ExpenseResponse>> updateExpense(
            @PathVariable Long tripId, @PathVariable Long expenseId,
            @Valid @RequestBody CreateExpenseRequest request) {
        return ResponseEntity.ok(ApiResponse.success(
                expenseService.updateExpense(tripId, expenseId, securityUtils.getCurrentUser(), request)));
    }

    @DeleteMapping("/{expenseId}")
    @Operation(summary = "Xóa chi phí")
    public ResponseEntity<ApiResponse<Map<String, String>>> deleteExpense(
            @PathVariable Long tripId, @PathVariable Long expenseId) {
        expenseService.deleteExpense(tripId, expenseId, securityUtils.getCurrentUser());
        return ResponseEntity.ok(ApiResponse.success(Map.of("message", "Đã xóa chi phí")));
    }

    @GetMapping("/summary")
    @Operation(summary = "Tổng kết chi phí theo danh mục")
    public ResponseEntity<ApiResponse<ExpenseSummaryResponse>> getSummary(
            @PathVariable Long tripId) {
        return ResponseEntity.ok(ApiResponse.success(
                expenseService.getSummary(tripId, securityUtils.getCurrentUser())));
    }

    @GetMapping("/balances")
    @Operation(summary = "Bảng quyết toán (ai nợ ai)")
    public ResponseEntity<ApiResponse<BalanceResponse>> getBalances(@PathVariable Long tripId) {
        return ResponseEntity.ok(ApiResponse.success(
                expenseService.getBalances(tripId, securityUtils.getCurrentUser())));
    }

    @PatchMapping("/splits/{splitId}/settle")
    @Operation(summary = "Đánh dấu đã thanh toán")
    public ResponseEntity<ApiResponse<Map<String, String>>> settleSplit(
            @PathVariable Long tripId, @PathVariable Long splitId) {
        expenseService.settleSplit(tripId, splitId, securityUtils.getCurrentUser());
        return ResponseEntity.ok(ApiResponse.success(Map.of("message", "Đã đánh dấu thanh toán")));
    }
}
