package com.travelmate.domain.trip.dto;

import com.travelmate.common.enums.TripRole;
import com.travelmate.domain.trip.entity.TripMember;
import java.time.LocalDateTime;

public record MemberResponse(
        Long memberId,
        Long userId,
        String fullName,
        String email,
        String avatarUrl,
        TripRole role,
        LocalDateTime joinedAt
) {
    public static MemberResponse from(TripMember tm) {
        return new MemberResponse(
                tm.getId(),
                tm.getUser().getId(),
                tm.getUser().getFullName(),
                tm.getUser().getEmail(),
                tm.getUser().getAvatarUrl(),
                tm.getRole(),
                tm.getJoinedAt()
        );
    }
}
