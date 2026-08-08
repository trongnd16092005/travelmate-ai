package com.travelmate.domain.trip.dto;

import com.travelmate.common.enums.TripRole;
import jakarta.validation.constraints.NotNull;

public record UpdateMemberRoleRequest(
        @NotNull(message = "Vai trò không được để trống")
        TripRole role
) {}
