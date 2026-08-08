package com.travelmate.domain.itinerary.dto;

import com.travelmate.domain.itinerary.entity.ItineraryDay;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public record ItineraryDayResponse(
        Long id,
        Integer dayNumber,
        LocalDate date,
        String note,
        List<ActivityResponse> activities,
        BigDecimal totalEstimatedCost
) {
    public static ItineraryDayResponse from(ItineraryDay day) {
        List<ActivityResponse> activities = day.getActivities().stream()
                .map(ActivityResponse::from).toList();
        BigDecimal total = activities.stream()
                .filter(a -> a.estimatedCost() != null)
                .map(ActivityResponse::estimatedCost)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        return new ItineraryDayResponse(
                day.getId(), day.getDayNumber(), day.getDate(),
                day.getNote(), activities, total);
    }
}
