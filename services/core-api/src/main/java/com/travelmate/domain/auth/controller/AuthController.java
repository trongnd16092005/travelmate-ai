package com.travelmate.domain.auth.controller;

import com.travelmate.common.response.ApiResponse;
import com.travelmate.domain.auth.dto.*;
import com.travelmate.domain.auth.service.AuthService;
import com.travelmate.security.SecurityUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
@Tag(name = "Authentication", description = "API xác thực người dùng")
public class AuthController {

    private final AuthService authService;
    private final SecurityUtils securityUtils;

    @PostMapping("/register")
    @Operation(summary = "Đăng ký tài khoản mới")
    public ResponseEntity<ApiResponse<Map<String, String>>> register(
            @Valid @RequestBody RegisterRequest request) {
        String message = authService.register(request);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success(Map.of("message", message)));
    }

    @GetMapping("/verify-email")
    @Operation(summary = "Xác minh email qua token")
    public ResponseEntity<ApiResponse<Map<String, String>>> verifyEmail(
            @RequestParam String token) {
        String message = authService.verifyEmail(token);
        return ResponseEntity.ok(ApiResponse.success(Map.of("message", message)));
    }

    @PostMapping("/resend-verification")
    @Operation(summary = "Gửi lại email xác minh")
    public ResponseEntity<ApiResponse<Map<String, String>>> resendVerification(
            @RequestBody Map<String, String> body) {
        authService.resendVerificationEmail(body.getOrDefault("email", ""));
        return ResponseEntity.ok(ApiResponse.success(
                Map.of("message", "Email xác minh đã được gửi nếu địa chỉ này tồn tại")));
    }

    @PostMapping("/login")
    @Operation(summary = "Đăng nhập")
    public ResponseEntity<ApiResponse<AuthResponse>> login(
            @Valid @RequestBody LoginRequest request,
            HttpServletRequest httpRequest) {
        String deviceInfo = httpRequest.getHeader("User-Agent");
        AuthResponse response = authService.login(request, deviceInfo);
        return ResponseEntity.ok(ApiResponse.success(response, "Đăng nhập thành công"));
    }

    @PostMapping("/refresh")
    @Operation(summary = "Làm mới access token")
    public ResponseEntity<ApiResponse<Map<String, Object>>> refreshToken(
            @Valid @RequestBody RefreshTokenRequest request) {
        String newAccessToken = authService.refreshAccessToken(request.refreshToken());
        return ResponseEntity.ok(ApiResponse.success(Map.of(
                "accessToken", newAccessToken,
                "tokenType", "Bearer",
                "expiresIn", 900
        )));
    }

    @PostMapping("/logout")
    @Operation(summary = "Đăng xuất")
    public ResponseEntity<ApiResponse<Map<String, String>>> logout(
            @RequestBody(required = false) RefreshTokenRequest request) {
        if (request != null) {
            authService.logout(request.refreshToken(), securityUtils.getCurrentUser());
        }
        return ResponseEntity.ok(ApiResponse.success(Map.of("message", "Đăng xuất thành công")));
    }

    @PostMapping("/logout-all")
    @Operation(summary = "Đăng xuất tất cả thiết bị")
    public ResponseEntity<ApiResponse<Map<String, String>>> logoutAll() {
        authService.logoutAll(securityUtils.getCurrentUser());
        return ResponseEntity.ok(ApiResponse.success(
                Map.of("message", "Đã đăng xuất khỏi tất cả thiết bị")));
    }

    @PostMapping("/forgot-password")
    @Operation(summary = "Yêu cầu OTP đặt lại mật khẩu")
    public ResponseEntity<ApiResponse<Map<String, String>>> forgotPassword(
            @Valid @RequestBody ForgotPasswordRequest request) {
        authService.forgotPassword(request);
        return ResponseEntity.ok(ApiResponse.success(
                Map.of("message", "OTP đã được gửi nếu email tồn tại trong hệ thống")));
    }

    @PostMapping("/reset-password")
    @Operation(summary = "Đặt lại mật khẩu bằng OTP")
    public ResponseEntity<ApiResponse<Map<String, String>>> resetPassword(
            @Valid @RequestBody ResetPasswordRequest request) {
        authService.resetPassword(request);
        return ResponseEntity.ok(ApiResponse.success(
                Map.of("message", "Mật khẩu đã được đặt lại thành công")));
    }
}
