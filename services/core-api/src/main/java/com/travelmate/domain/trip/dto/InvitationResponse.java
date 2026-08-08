package com.travelmate.domain.trip.dto;

import com.travelmate.common.enums.InvitationStatus;
import com.travelmate.common.enums.TripRole;
import com.travelmate.domain.trip.entity.Invitation;
import java.time.LocalDateTime;

public record InvitationResponse(
        Long id,
        String inviteeEmail,
        TripRole role,
        InvitationStatus status,
        LocalDateTime expiresAt
) {
    public static InvitationResponse from(Invitation inv) {
        return new InvitationResponse(inv.getId(), inv.getInviteeEmail(),
                inv.getRole(), inv.getStatus(), inv.getExpiresAt());
    }
}
