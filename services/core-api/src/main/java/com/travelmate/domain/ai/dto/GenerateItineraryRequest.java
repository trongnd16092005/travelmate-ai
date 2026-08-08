package com.travelmate.domain.ai.dto;

import com.travelmate.common.enums.TravelStyle;
import jakarta.validation.constraints.NotNull;

import java.util.List;

public record GenerateItineraryRequest(
        @NotNull Long tripId,
        TravelStyle travelStyle,
        List<String> interests,
        String specialRequests
) {}
