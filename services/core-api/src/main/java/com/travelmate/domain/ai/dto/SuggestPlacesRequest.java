package com.travelmate.domain.ai.dto;

import jakarta.validation.constraints.NotBlank;

public record SuggestPlacesRequest(
        @NotBlank String city,
        String type,         // RESTAURANT, HOTEL, CAFE...
        Long budget,         // per person in VND
        Long tripId,
        String specialNote,
        int count
) {}
