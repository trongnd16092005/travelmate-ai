package com.travelmate.domain.trip.dto;

import com.travelmate.common.enums.TravelStyle;
import jakarta.validation.constraints.*;
import java.math.BigDecimal;
import java.time.LocalDate;

public record UpdateTripRequest(
        @Size(max = 100) String name,
        @Size(max = 255) String destination,
        LocalDate startDate,
        LocalDate endDate,
        @Min(0) BigDecimal budget,
        @Min(1) @Max(100) Integer numPeople,
        TravelStyle travelStyle,
        @Size(max = 2000) String description
) {}
