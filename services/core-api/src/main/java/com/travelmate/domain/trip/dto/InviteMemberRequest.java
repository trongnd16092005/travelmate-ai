package com.travelmate.domain.trip.dto;

import com.travelmate.common.enums.TripRole;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record InviteMemberRequest(
        @NotBlank @Email(message = "Email không hợp lệ")
        String email,

        @NotNull(message = "Vai trò không được để trống")
        TripRole role
) {}
