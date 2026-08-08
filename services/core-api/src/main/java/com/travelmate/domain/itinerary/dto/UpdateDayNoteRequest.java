package com.travelmate.domain.itinerary.dto;

import jakarta.validation.constraints.Size;

public record UpdateDayNoteRequest(
        @Size(max = 2000)
        String note
) {}
