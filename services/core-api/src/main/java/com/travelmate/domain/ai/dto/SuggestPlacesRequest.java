package com.travelmate.domain.ai.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

public record SuggestPlacesRequest(
        @NotBlank String city,
        String type,         // RESTAURANT, HOTEL, CAFE...
        String specialNote,
        @Min(1) @Max(6) Integer count
) {}
