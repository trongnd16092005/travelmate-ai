package com.travelmate.domain.trip.repository;

import com.travelmate.common.enums.InvitationStatus;
import com.travelmate.domain.trip.entity.Invitation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.Optional;

public interface InvitationRepository extends JpaRepository<Invitation, Long> {

    Optional<Invitation> findByToken(String token);

    List<Invitation> findAllByTripIdAndStatus(Long tripId, InvitationStatus status);

    boolean existsByTripIdAndInviteeEmailAndStatus(Long tripId, String email, InvitationStatus status);

    @Modifying
    @Query("UPDATE Invitation i SET i.status = 'EXPIRED' WHERE i.status = 'PENDING' AND i.expiresAt < CURRENT_TIMESTAMP")
    int expireStaleInvitations();
}
