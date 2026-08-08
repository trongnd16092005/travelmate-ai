package com.travelmate.domain.place.repository;

import com.travelmate.domain.place.entity.SavedPlace;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface SavedPlaceRepository extends JpaRepository<SavedPlace, Long> {
    List<SavedPlace> findAllByTripId(Long tripId);
    Optional<SavedPlace> findByTripIdAndPlaceId(Long tripId, Long placeId);
    boolean existsByTripIdAndPlaceId(Long tripId, Long placeId);
}
