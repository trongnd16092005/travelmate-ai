package com.travelmate.domain.auth.dto;

import com.travelmate.common.enums.UserRole;

public record AuthResponse(
        String accessToken,
        String refreshToken,
        String tokenType,
        long expiresIn,
        UserInfo user
) {
    public static final String BEARER = "Bearer";

    public record UserInfo(
            Long id,
            String fullName,
            String email,
            String avatarUrl,
            UserRole role
    ) {}
}
