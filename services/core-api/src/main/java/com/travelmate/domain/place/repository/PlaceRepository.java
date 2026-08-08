package com.travelmate.domain.place.repository;

import com.travelmate.common.enums.PlaceType;
import com.travelmate.domain.place.entity.Place;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface PlaceRepository extends JpaRepository<Place, Long> {

    @Query("""  
            SELECT p FROM Place p
            WHERE (:city IS NULL OR LOWER(p.city) LIKE LOWER(CONCAT('%',:city,'%')))
            AND (:type IS NULL OR p.type = :type)
            AND (:keyword IS NULL
                 OR LOWER(p.name) LIKE LOWER(CONCAT('%',:keyword,'%'))
                 OR LOWER(p.address) LIKE LOWER(CONCAT('%',:keyword,'%')))
            ORDER BY p.rating DESC NULLS LAST
            """)
    Page<Place> searchPlaces(@Param("keyword") String keyword,
                              @Param("city") String city,
                              @Param("type") PlaceType type,
                              Pageable pageable);
}
