package com.travelmate.domain.itinerary.dto;

import com.travelmate.common.enums.ActivityStatus;
import jakarta.validation.constraints.NotNull;

public record UpdateActivityStatusRequest(
        @NotNull(message = "Trạng thái không được để trống")
        ActivityStatus status
) {}
