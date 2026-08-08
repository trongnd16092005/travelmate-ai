package com.travelmate.domain.trip.dto;

import com.travelmate.common.enums.TripRole;
import com.travelmate.common.enums.TripStatus;
import com.travelmate.common.enums.TravelStyle;
import com.travelmate.domain.trip.entity.Trip;
import com.travelmate.domain.trip.entity.TripMember;

import java.math.BigDecimal;
import java.time.LocalDate;

public record TripSummaryResponse(
        Long id,
        String name,
        String destination,
        String coverImageUrl,
        LocalDate startDate,
        LocalDate endDate,
        BigDecimal budget,
        Integer numPeople,
        TripStatus status,
        TravelStyle travelStyle,
        TripRole myRole,
        long memberCount,
        long durationDays
) {
    public static TripSummaryResponse from(Trip trip, TripMember myMembership, long memberCount) {
        return new TripSummaryResponse(
                trip.getId(), trip.getName(), trip.getDestination(),
                trip.getCoverImageUrl(), trip.getStartDate(), trip.getEndDate(),
                trip.getBudget(), trip.getNumPeople(), trip.getStatus(),
                trip.getTravelStyle(),
                myMembership != null ? myMembership.getRole() : null,
                memberCount,
                trip.getDurationDays()
        );
    }
}
