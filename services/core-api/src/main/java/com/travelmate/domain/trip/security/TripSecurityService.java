package com.travelmate.domain.trip.security;

import com.travelmate.common.enums.TripRole;
import com.travelmate.domain.trip.repository.TripMemberRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class TripSecurityService {

    private final TripMemberRepository tripMemberRepository;

    public boolean isMember(Long tripId, Authentication auth) {
        Long userId = Long.parseLong(auth.getName());
        return tripMemberRepository.existsByTripIdAndUserId(tripId, userId);
    }

    public boolean isOwnerOrEditor(Long tripId, Authentication auth) {
        Long userId = Long.parseLong(auth.getName());
        return tripMemberRepository.existsByTripIdAndUserIdAndRoleIn(
                tripId, userId, List.of(TripRole.OWNER, TripRole.EDITOR));
    }

    public boolean isOwner(Long tripId, Authentication auth) {
        Long userId = Long.parseLong(auth.getName());
        return tripMemberRepository.existsByTripIdAndUserIdAndRole(
                tripId, userId, TripRole.OWNER);
    }
}
