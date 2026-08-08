package com.travelmate.domain.admin.dto;

import com.travelmate.common.enums.AccountStatus;
import com.travelmate.common.enums.UserRole;
import com.travelmate.domain.user.entity.User;
import java.time.LocalDateTime;

public record AdminUserResponse(
        Long id, String fullName, String email, String avatarUrl,
        UserRole role, AccountStatus status,
        boolean emailVerified, LocalDateTime createdAt, LocalDateTime deletedAt
) {
    public static AdminUserResponse from(User u) {
        return new AdminUserResponse(
                u.getId(), u.getFullName(), u.getEmail(), u.getAvatarUrl(),
                u.getRole(), u.getStatus(), u.isEmailVerified(),
                u.getCreatedAt(), u.getDeletedAt());
    }
}
