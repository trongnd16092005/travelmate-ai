package com.travelmate.domain.user.dto;

import com.travelmate.common.enums.AccountStatus;
import com.travelmate.common.enums.TravelStyle;
import com.travelmate.common.enums.UserRole;
import com.travelmate.domain.user.entity.User;

import java.time.LocalDateTime;

public record UserProfileResponse(
        Long id,
        String fullName,
        String email,
        String avatarUrl,
        String bio,
        UserRole role,
        AccountStatus status,
        TravelStyle travelStyle,
        boolean emailVerified,
        LocalDateTime createdAt
) {
    public static UserProfileResponse from(User user) {
        return new UserProfileResponse(
                user.getId(), user.getFullName(), user.getEmail(),
                user.getAvatarUrl(), user.getBio(), user.getRole(),
                user.getStatus(), user.getTravelStyle(),
                user.isEmailVerified(), user.getCreatedAt()
        );
    }
}
