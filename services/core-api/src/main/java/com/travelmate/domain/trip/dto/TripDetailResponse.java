package com.travelmate.domain.trip.dto;

import com.travelmate.common.enums.TripRole;
import com.travelmate.common.enums.TripStatus;
import com.travelmate.common.enums.TravelStyle;
import com.travelmate.domain.trip.entity.Trip;
import com.travelmate.domain.trip.entity.TripMember;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

public record TripDetailResponse(
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
        String description,
        TripRole myRole,
        long durationDays,
        boolean isPublic,
        String publicToken,
        OwnerInfo owner,
        List<MemberResponse> members,
        LocalDateTime createdAt
) {
    public record OwnerInfo(Long id, String fullName, String avatarUrl) {}

    public static TripDetailResponse from(Trip trip, TripMember myMembership, List<MemberResponse> members) {
        return new TripDetailResponse(
                trip.getId(), trip.getName(), trip.getDestination(),
                trip.getCoverImageUrl(), trip.getStartDate(), trip.getEndDate(),
                trip.getBudget(), trip.getNumPeople(), trip.getStatus(),
                trip.getTravelStyle(), trip.getDescription(),
                myMembership != null ? myMembership.getRole() : null,
                trip.getDurationDays(),
                trip.getIsPublic(),
                trip.getIsPublic() ? trip.getPublicToken() : null,
                new OwnerInfo(trip.getOwner().getId(), trip.getOwner().getFullName(), trip.getOwner().getAvatarUrl()),
                members,
                trip.getCreatedAt()
        );
    }
}
