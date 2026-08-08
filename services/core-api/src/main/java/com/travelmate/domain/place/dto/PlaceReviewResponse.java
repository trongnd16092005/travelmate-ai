package com.travelmate.domain.place.dto;

import com.travelmate.domain.place.entity.PlaceReview;
import java.time.LocalDateTime;

public record PlaceReviewResponse(
        Long id, Long userId, String userName, String avatarUrl,
        Integer rating, String comment, LocalDateTime createdAt
) {
    public static PlaceReviewResponse from(PlaceReview r) {
        return new PlaceReviewResponse(r.getId(), r.getUser().getId(),
                r.getUser().getFullName(), r.getUser().getAvatarUrl(),
                r.getRating(), r.getComment(), r.getCreatedAt());
    }
}
