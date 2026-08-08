package com.travelmate.domain.admin.controller;

import com.travelmate.common.response.ApiResponse;
import com.travelmate.common.response.PageResponse;
import com.travelmate.domain.admin.dto.*;
import com.travelmate.domain.admin.service.AdminService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/admin")
@RequiredArgsConstructor
@PreAuthorize("hasRole('ADMIN')")
@Tag(name = "Admin", description = "API quản trị hệ thống")
@SecurityRequirement(name = "bearerAuth")
public class AdminController {

    private final AdminService adminService;

    @GetMapping("/dashboard/stats")
    @Operation(summary = "Thống kê tổng quan dashboard")
    public ResponseEntity<ApiResponse<DashboardStatsResponse>> getStats() {
        return ResponseEntity.ok(ApiResponse.success(adminService.getDashboardStats()));
    }

    @GetMapping("/users")
    @Operation(summary = "Danh sách người dùng")
    public ResponseEntity<ApiResponse<PageResponse<AdminUserResponse>>> getUsers(
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(ApiResponse.success(
                adminService.getUsers(keyword, status, page, size)));
    }

    @GetMapping("/users/{userId}")
    @Operation(summary = "Chi tiết người dùng")
    public ResponseEntity<ApiResponse<AdminUserResponse>> getUser(@PathVariable Long userId) {
        return ResponseEntity.ok(ApiResponse.success(adminService.getUser(userId)));
    }

    @PatchMapping("/users/{userId}/status")
    @Operation(summary = "Khoá/Mở khoá tài khoản")
    public ResponseEntity<ApiResponse<AdminUserResponse>> updateStatus(
            @PathVariable Long userId, @Valid @RequestBody UpdateUserStatusRequest request) {
        return ResponseEntity.ok(ApiResponse.success(
                adminService.updateUserStatus(userId, request), "Đã cập nhật trạng thái"));
    }

    @DeleteMapping("/users/{userId}")
    @Operation(summary = "Xóa tài khoản")
    public ResponseEntity<ApiResponse<Map<String, String>>> deleteUser(@PathVariable Long userId) {
        adminService.deleteUser(userId);
        return ResponseEntity.ok(ApiResponse.success(Map.of("message", "Đã xóa tài khoản")));
    }
}
