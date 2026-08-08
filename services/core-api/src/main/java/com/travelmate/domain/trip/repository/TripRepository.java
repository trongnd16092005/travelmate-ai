package com.travelmate.domain.trip.repository;

import com.travelmate.common.enums.TripStatus;
import com.travelmate.domain.trip.entity.Trip;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Optional;

public interface TripRepository extends JpaRepository<Trip, Long> {

    // Tất cả trips mà user là thành viên (owner hoặc member)
    @Query("""  
            SELECT DISTINCT t FROM Trip t
            JOIN TripMember tm ON tm.trip = t
            WHERE tm.user.id = :userId
            AND (:status IS NULL OR t.status = :status)
            AND (:keyword IS NULL OR LOWER(t.name) LIKE LOWER(CONCAT('%',:keyword,'%'))
                 OR LOWER(t.destination) LIKE LOWER(CONCAT('%',:keyword,'%')))
            ORDER BY t.startDate DESC
            """)
    Page<Trip> findAllByMember(@Param("userId") Long userId,
                               @Param("status") TripStatus status,
                               @Param("keyword") String keyword,
                               Pageable pageable);

    Optional<Trip> findByPublicToken(String publicToken);

    @Query("SELECT t FROM Trip t JOIN TripMember tm ON tm.trip = t WHERE t.id = :tripId AND tm.user.id = :userId")
    Optional<Trip> findByIdAndMemberId(@Param("tripId") Long tripId, @Param("userId") Long userId);
}
