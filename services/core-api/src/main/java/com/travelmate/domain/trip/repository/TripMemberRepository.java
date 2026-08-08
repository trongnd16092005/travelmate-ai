package com.travelmate.domain.trip.repository;

import com.travelmate.common.enums.TripRole;
import com.travelmate.domain.trip.entity.TripMember;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface TripMemberRepository extends JpaRepository<TripMember, Long> {

    Optional<TripMember> findByTripIdAndUserId(Long tripId, Long userId);

    boolean existsByTripIdAndUserId(Long tripId, Long userId);

    boolean existsByTripIdAndUserIdAndRoleIn(Long tripId, Long userId, List<TripRole> roles);

    boolean existsByTripIdAndUserIdAndRole(Long tripId, Long userId, TripRole role);

    List<TripMember> findAllByTripId(Long tripId);

    long countByTripId(Long tripId);

    @Modifying
    @Query("DELETE FROM TripMember tm WHERE tm.trip.id = :tripId AND tm.user.id = :userId AND tm.role != 'OWNER'")
    void deleteByTripIdAndUserIdNotOwner(@Param("tripId") Long tripId, @Param("userId") Long userId);
}
