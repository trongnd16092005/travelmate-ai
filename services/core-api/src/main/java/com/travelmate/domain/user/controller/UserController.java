package com.travelmate.domain.user.controller;

import com.travelmate.common.response.ApiResponse;
import com.travelmate.domain.user.dto.*;
import com.travelmate.domain.user.service.UserService;
import com.travelmate.security.SecurityUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@Tag(name = "Users", description = "API quản lý người dùng")
@SecurityRequirement(name = "bearerAuth")
public class UserController {

    private final UserService userService;
    private final SecurityUtils securityUtils;

    @GetMapping("/me")
    @Operation(summary = "Lấy thông tin profile cá nhân")
    public ResponseEntity<ApiResponse<UserProfileResponse>> getMyProfile() {
        var user = securityUtils.getCurrentUser();
        return ResponseEntity.ok(ApiResponse.success(userService.getProfile(user)));
    }

    @PutMapping("/me")
    @Operation(summary = "Cập nhật profile")
    public ResponseEntity<ApiResponse<UserProfileResponse>> updateProfile(
            @Valid @RequestBody UpdateProfileRequest request) {
        var user = securityUtils.getCurrentUser();
        return ResponseEntity.ok(ApiResponse.success(userService.updateProfile(user, request),
                "Cập nhật profile thành công"));
    }

    @PutMapping("/me/password")
    @Operation(summary = "Đổi mật khẩu")
    public ResponseEntity<ApiResponse<Map<String, String>>> changePassword(
            @Valid @RequestBody ChangePasswordRequest request) {
        var user = securityUtils.getCurrentUser();
        userService.changePassword(user, request);
        return ResponseEntity.ok(ApiResponse.success(
                Map.of("message", "Đổi mật khẩu thành công")));
    }

    @DeleteMapping("/me")
    @Operation(summary = "Xóa tài khoản (soft delete)")
    public ResponseEntity<ApiResponse<Map<String, String>>> deleteAccount() {
        var user = securityUtils.getCurrentUser();
        userService.softDelete(user);
        return ResponseEntity.ok(ApiResponse.success(
                Map.of("message", "Tài khoản sẽ bị xóa sau 30 ngày")));
    }
}
