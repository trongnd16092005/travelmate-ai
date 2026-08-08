package com.travelmate.domain.trip.entity;

import com.travelmate.common.enums.TripStatus;
import com.travelmate.common.enums.TravelStyle;
import com.travelmate.domain.user.entity.User;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

@Entity
@Table(name = "trips", indexes = {
        @Index(name = "idx_trips_owner_id", columnList = "owner_id"),
        @Index(name = "idx_trips_status", columnList = "status")
})
@Getter @Setter @Builder @NoArgsConstructor @AllArgsConstructor
public class Trip {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(nullable = false, length = 255)
    private String destination;

    @Column(name = "cover_image_url", length = 500)
    private String coverImageUrl;

    @Column(name = "start_date", nullable = false)
    private LocalDate startDate;

    @Column(name = "end_date", nullable = false)
    private LocalDate endDate;

    @Column(precision = 15, scale = 2)
    private BigDecimal budget;

    @Column(name = "num_people", nullable = false)
    @Builder.Default
    private Integer numPeople = 1;

    @Enumerated(EnumType.STRING)
    @Column(name = "travel_style", length = 30)
    private TravelStyle travelStyle;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private TripStatus status = TripStatus.UPCOMING;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "owner_id", nullable = false)
    private User owner;

    @Column(name = "is_public", nullable = false)
    @Builder.Default
    private Boolean isPublic = false;

    @Column(name = "public_token", unique = true, length = 64)
    private String publicToken;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    public long getDurationDays() {
        return ChronoUnit.DAYS.between(startDate, endDate) + 1;
    }

    public boolean isUpcoming() {
        return LocalDate.now().isBefore(startDate);
    }

    public boolean isOngoing() {
        LocalDate today = LocalDate.now();
        return !today.isBefore(startDate) && !today.isAfter(endDate);
    }

    public void updateStatus() {
        if (isUpcoming()) this.status = TripStatus.UPCOMING;
        else if (isOngoing()) this.status = TripStatus.ONGOING;
        else this.status = TripStatus.COMPLETED;
    }
}
