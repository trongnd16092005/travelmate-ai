package com.travelmate.domain.itinerary.dto;

import java.math.BigDecimal;
import java.util.List;

public record FullItineraryResponse(
        Long tripId,
        List<ItineraryDayResponse> days,
        BigDecimal totalEstimatedCost
) {}
