package com.travelmate.domain.admin.dto;

import com.travelmate.common.enums.AccountStatus;
import jakarta.validation.constraints.NotNull;

public record UpdateUserStatusRequest(
        @NotNull AccountStatus status
) {}
