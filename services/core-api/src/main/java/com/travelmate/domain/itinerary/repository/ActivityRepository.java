package com.travelmate.domain.itinerary.repository;

import com.travelmate.domain.itinerary.entity.Activity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface ActivityRepository extends JpaRepository<Activity, Long> {

    List<Activity> findAllByItineraryDayIdOrderBySortOrderAsc(Long dayId);

    @Query("SELECT MAX(a.sortOrder) FROM Activity a WHERE a.itineraryDay.id = :dayId")
    Integer findMaxSortOrder(@Param("dayId") Long dayId);

    @Modifying
    @Query("UPDATE Activity a SET a.sortOrder = :order WHERE a.id = :id")
    void updateSortOrder(@Param("id") Long id, @Param("order") int order);
}
