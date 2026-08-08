package com.travelmate.domain.itinerary.repository;

import com.travelmate.domain.itinerary.entity.ItineraryDay;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface ItineraryDayRepository extends JpaRepository<ItineraryDay, Long> {

    List<ItineraryDay> findAllByTripIdOrderByDayNumberAsc(Long tripId);

    Optional<ItineraryDay> findByIdAndTripId(Long id, Long tripId);

    @Query("SELECT MAX(d.dayNumber) FROM ItineraryDay d WHERE d.trip.id = :tripId")
    Optional<Integer> findMaxDayNumber(@Param("tripId") Long tripId);

    void deleteAllByTripId(Long tripId);
}
