package com.travelmate.domain.itinerary.dto;

import com.travelmate.common.enums.ActivityType;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;
import java.time.LocalTime;

public record ActivityRequest(
        @NotBlank(message = "Tên hoạt động không được để trống")
        @Size(max = 255)
        String name,

        ActivityType type,

        Long placeId,

        LocalTime startTime,
        LocalTime endTime,

        BigDecimal estimatedCost,

        @Size(max = 2000)
        String description,

        @Size(max = 2000)
        String note,

        Integer sortOrder
) {}
