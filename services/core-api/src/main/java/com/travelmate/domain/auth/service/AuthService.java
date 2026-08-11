package com.travelmate.domain.auth.service;

import com.travelmate.common.enums.AccountStatus;
import com.travelmate.common.exception.AppException;
import com.travelmate.domain.auth.dto.*;
import com.travelmate.domain.auth.entity.EmailVerification;
import com.travelmate.domain.auth.entity.RefreshToken;
import com.travelmate.domain.auth.repository.EmailVerificationRepository;
import com.travelmate.domain.auth.repository.RefreshTokenRepository;
import com.travelmate.domain.user.entity.User;
import com.travelmate.domain.user.repository.UserRepository;
import com.travelmate.security.JwtProperties;
import com.travelmate.security.JwtService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class AuthService {

    private final UserRepository userRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final EmailVerificationRepository emailVerificationRepository;
    private final JwtService jwtService;
    private final JwtProperties jwtProperties;
    private final PasswordEncoder passwordEncoder;
    private final EmailService emailService;

    @Value("${app.auth.require-email-verification:true}")
    private boolean requireEmailVerification;

    // ─── REGISTER ───────────────────────────────────────────────
    public String register(RegisterRequest request) {
        // Validate confirm password
        if (!request.password().equals(request.confirmPassword())) {
            throw AppException.badRequest("PASSWORD_MISMATCH", "Mật khẩu xác nhận không khớp");
        }

        // Check email duplicate
        if (userRepository.existsByEmailAndDeletedAtIsNull(request.email())) {
            throw AppException.conflict("EMAIL_ALREADY_EXISTS", "Email đã được sử dụng");
        }

        // Create user
        User user = User.builder()
                .fullName(request.fullName())
                .email(request.email().toLowerCase())
                .passwordHash(passwordEncoder.encode(request.password()))
                .status(requireEmailVerification ? AccountStatus.PENDING : AccountStatus.ACTIVE)
                .emailVerifiedAt(requireEmailVerification ? null : LocalDateTime.now())
                .build();
        userRepository.save(user);

        if (requireEmailVerification) {
            sendVerificationEmail(user);
        }

        return requireEmailVerification
                ? "Đăng ký thành công. Vui lòng kiểm tra email để xác minh tài khoản."
                : "Đăng ký thành công. Bạn có thể đăng nhập ngay.";
    }

    @Async
    protected void sendVerificationEmail(User user) {
        try {
            String token = UUID.randomUUID().toString();
            EmailVerification verification = EmailVerification.builder()
                    .user(user)
                    .token(token)
                    .expiresAt(LocalDateTime.now().plusHours(24))
                    .build();
            emailVerificationRepository.save(verification);
            emailService.sendVerificationEmail(user.getEmail(), user.getFullName(), token);
        } catch (Exception e) {
            log.error("Failed to send verification email to {}: {}", user.getEmail(), e.getMessage());
        }
    }

    // ─── VERIFY EMAIL ────────────────────────────────────────────
    public String verifyEmail(String token) {
        EmailVerification verification = emailVerificationRepository
                .findByTokenAndIsUsedFalse(token)
                .orElseThrow(() -> AppException.badRequest("INVALID_VERIFICATION_TOKEN",
                        "Link xác minh không hợp lệ hoặc đã được sử dụng"));

        if (verification.isExpired()) {
            throw AppException.badRequest("VERIFICATION_TOKEN_EXPIRED",
                    "Link xác minh đã hết hạn. Vui lòng yêu cầu gửi lại email.");
        }

        User user = verification.getUser();
        user.setStatus(AccountStatus.ACTIVE);
        user.setEmailVerifiedAt(LocalDateTime.now());
        userRepository.save(user);

        verification.setIsUsed(true);
        emailVerificationRepository.save(verification);

        return "Xác minh email thành công! Bạn có thể đăng nhập ngay.";
    }

    // ─── LOGIN ───────────────────────────────────────────────────
    public AuthResponse login(LoginRequest request, String deviceInfo) {
        User user = userRepository.findByEmailAndDeletedAtIsNull(request.email().toLowerCase())
                .orElseThrow(() -> AppException.unauthorized("INVALID_CREDENTIALS",
                        "Email hoặc mật khẩu không đúng"));

        // Check account locked
        if (user.isLocked()) {
            String msg = user.getLockedUntil() != null
                    ? "Tài khoản tạm khoá đến " + user.getLockedUntil()
                    : "Tài khoản bị khoá";
            throw AppException.unauthorized("ACCOUNT_LOCKED", msg);
        }

        // Check email verified
        if (!user.isEmailVerified()) {
            throw AppException.unauthorized("EMAIL_NOT_VERIFIED",
                    "Email chưa được xác minh. Vui lòng kiểm tra hộp thư.");
        }

        // Verify password
        if (!passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            user.incrementFailedAttempts();
            userRepository.save(user);
            throw AppException.unauthorized("INVALID_CREDENTIALS", "Email hoặc mật khẩu không đúng");
        }

        // Reset failed attempts
        user.resetFailedAttempts();
        userRepository.save(user);

        return buildAuthResponse(user, deviceInfo);
    }

    private AuthResponse buildAuthResponse(User user, String deviceInfo) {
        String accessToken = jwtService.generateAccessToken(user);
        String refreshTokenValue = UUID.randomUUID().toString();

        RefreshToken refreshToken = RefreshToken.builder()
                .user(user)
                .token(refreshTokenValue)
                .expiresAt(LocalDateTime.now().plusSeconds(
                        jwtProperties.getRefreshTokenExpiration() / 1000))
                .deviceInfo(deviceInfo)
                .build();
        refreshTokenRepository.save(refreshToken);

        return new AuthResponse(
                accessToken,
                refreshTokenValue,
                AuthResponse.BEARER,
                jwtProperties.getAccessTokenExpiration() / 1000,
                new AuthResponse.UserInfo(
                        user.getId(), user.getFullName(),
                        user.getEmail(), user.getAvatarUrl(), user.getRole()
                )
        );
    }

    // ─── REFRESH TOKEN ───────────────────────────────────────────
    public AuthResponse.UserInfo refreshToken(RefreshTokenRequest request) {
        RefreshToken storedToken = refreshTokenRepository
                .findByTokenAndIsRevokedFalse(request.refreshToken())
                .orElseThrow(() -> AppException.unauthorized("TOKEN_INVALID", "Refresh token không hợp lệ"));

        if (storedToken.isExpired()) {
            storedToken.revoke();
            refreshTokenRepository.save(storedToken);
            throw AppException.unauthorized("SESSION_EXPIRED",
                    "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại");
        }

        storedToken.setLastUsedAt(LocalDateTime.now());
        refreshTokenRepository.save(storedToken);

        String newAccessToken = jwtService.generateAccessToken(storedToken.getUser());
        // Return only new access token (wrap in record)
        return null; // Handled in controller
    }

    // Separate method returning the new access token string
    public String refreshAccessToken(String refreshTokenValue) {
        RefreshToken storedToken = refreshTokenRepository
                .findByTokenAndIsRevokedFalse(refreshTokenValue)
                .orElseThrow(() -> AppException.unauthorized("TOKEN_INVALID", "Refresh token không hợp lệ"));

        if (storedToken.isExpired()) {
            storedToken.revoke();
            refreshTokenRepository.save(storedToken);
            throw AppException.unauthorized("SESSION_EXPIRED",
                    "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại");
        }

        storedToken.setLastUsedAt(LocalDateTime.now());
        refreshTokenRepository.save(storedToken);

        return jwtService.generateAccessToken(storedToken.getUser());
    }

    // ─── LOGOUT ──────────────────────────────────────────────────
    public void logout(String refreshTokenValue, User currentUser) {
        refreshTokenRepository.findByTokenAndIsRevokedFalse(refreshTokenValue)
                .ifPresent(rt -> {
                    rt.revoke();
                    refreshTokenRepository.save(rt);
                });
    }

    public void logoutAll(User currentUser) {
        refreshTokenRepository.revokeAllByUser(currentUser);
    }

    // ─── FORGOT PASSWORD ─────────────────────────────────────────
    @Async
    public void forgotPassword(ForgotPasswordRequest request) {
        userRepository.findByEmailAndDeletedAtIsNull(request.email().toLowerCase())
                .ifPresent(user -> {
                    String otp = generateOtp();
                    // Store OTP in EmailVerification table reusing token field
                    EmailVerification ev = EmailVerification.builder()
                            .user(user)
                            .token("OTP:" + otp)
                            .expiresAt(LocalDateTime.now().plusMinutes(10))
                            .build();
                    emailVerificationRepository.save(ev);
                    emailService.sendPasswordResetEmail(user.getEmail(), user.getFullName(), otp);
                });
        // Always return success to prevent email enumeration
    }

    // ─── RESET PASSWORD ──────────────────────────────────────────
    public void resetPassword(ResetPasswordRequest request) {
        User user = userRepository.findByEmailAndDeletedAtIsNull(request.email().toLowerCase())
                .orElseThrow(() -> AppException.badRequest("USER_NOT_FOUND", "Email không tồn tại"));

        EmailVerification ev = emailVerificationRepository
                .findByTokenAndIsUsedFalse("OTP:" + request.otp())
                .orElseThrow(() -> AppException.badRequest("INVALID_OTP", "OTP không hợp lệ hoặc đã hết hạn"));

        if (!ev.getUser().getId().equals(user.getId())) {
            throw AppException.badRequest("INVALID_OTP", "OTP không hợp lệ");
        }

        if (ev.isExpired()) {
            throw AppException.badRequest("OTP_EXPIRED", "OTP đã hết hạn (10 phút)");
        }

        user.setPasswordHash(passwordEncoder.encode(request.newPassword()));
        userRepository.save(user);

        ev.setIsUsed(true);
        emailVerificationRepository.save(ev);

        // Revoke all refresh tokens
        refreshTokenRepository.revokeAllByUser(user);
    }

    // ─── RESEND VERIFICATION ─────────────────────────────────────
    @Async
    public void resendVerificationEmail(String email) {
        userRepository.findByEmailAndDeletedAtIsNull(email.toLowerCase())
                .filter(u -> !u.isEmailVerified())
                .ifPresent(user -> {
                    emailVerificationRepository.invalidateAllByUser(user);
                    sendVerificationEmail(user);
                });
    }

    private String generateOtp() {
        return String.format("%06d", (int) (Math.random() * 1000000));
    }
}
