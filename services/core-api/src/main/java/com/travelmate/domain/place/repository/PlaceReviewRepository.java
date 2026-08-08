package com.travelmate.domain.place.repository;

import com.travelmate.domain.place.entity.PlaceReview;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Optional;

public interface PlaceReviewRepository extends JpaRepository<PlaceReview, Long> {
    Page<PlaceReview> findAllByPlaceId(Long placeId, Pageable pageable);
    Optional<PlaceReview> findByPlaceIdAndUserId(Long placeId, Long userId);

    @Query("SELECT AVG(r.rating) FROM PlaceReview r WHERE r.place.id = :placeId")
    Double calculateAverageRating(@Param("placeId") Long placeId);
}
