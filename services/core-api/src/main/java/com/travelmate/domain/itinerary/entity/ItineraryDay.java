package com.travelmate.domain.itinerary.entity;

import com.travelmate.domain.trip.entity.Trip;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "itinerary_days",
        uniqueConstraints = @UniqueConstraint(columnNames = {"trip_id", "day_number"}),
        indexes = @Index(name = "idx_id_trip_id", columnList = "trip_id"))
@Getter @Setter @Builder @NoArgsConstructor @AllArgsConstructor
public class ItineraryDay {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "trip_id", nullable = false)
    private Trip trip;

    @Column(name = "day_number", nullable = false)
    private Integer dayNumber;

    @Column(nullable = false)
    private LocalDate date;

    @Column(columnDefinition = "TEXT")
    private String note;

    @OneToMany(mappedBy = "itineraryDay", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    @OrderBy("sortOrder ASC")
    @Builder.Default
    private List<Activity> activities = new ArrayList<>();
}
