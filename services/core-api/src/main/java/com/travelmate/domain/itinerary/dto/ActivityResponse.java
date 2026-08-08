package com.travelmate.domain.itinerary.dto;

import com.travelmate.common.enums.ActivityStatus;
import com.travelmate.common.enums.ActivityType;
import com.travelmate.domain.itinerary.entity.Activity;

import java.math.BigDecimal;
import java.time.LocalTime;

public record ActivityResponse(
        Long id,
        String name,
        ActivityType type,
        ActivityStatus status,
        LocalTime startTime,
        LocalTime endTime,
        Integer sortOrder,
        BigDecimal estimatedCost,
        String description,
        String note,
        String imageUrl,
        PlaceInfo place
) {
    public record PlaceInfo(Long id, String name, String address, Double rating, String imageUrl) {}

    public static ActivityResponse from(Activity a) {
        PlaceInfo placeInfo = null;
        if (a.getPlace() != null) {
            placeInfo = new PlaceInfo(
                    a.getPlace().getId(), a.getPlace().getName(),
                    a.getPlace().getAddress(), a.getPlace().getRating(),
                    a.getPlace().getImageUrl());
        }
        return new ActivityResponse(
                a.getId(), a.getName(), a.getType(), a.getStatus(),
                a.getStartTime(), a.getEndTime(), a.getSortOrder(),
                a.getEstimatedCost(), a.getDescription(), a.getNote(),
                a.getImageUrl(), placeInfo);
    }
}
