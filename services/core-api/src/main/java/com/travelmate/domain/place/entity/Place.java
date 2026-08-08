package com.travelmate.domain.place.entity;

import com.travelmate.common.enums.PlaceType;
import com.travelmate.domain.user.entity.User;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "places",
        indexes = {
            @Index(name = "idx_places_city", columnList = "city"),
            @Index(name = "idx_places_type", columnList = "type")
        })
@Getter @Setter @Builder @NoArgsConstructor @AllArgsConstructor
public class Place {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 255)
    private String name;

    @Column(length = 500)
    private String address;

    @Column(nullable = false, length = 100)
    private String city;

    @Column(nullable = false, length = 100)
    @Builder.Default
    private String country = "Vietnam";

    @Column(precision = 10, scale = 8)
    private Double latitude;

    @Column(precision = 11, scale = 8)
    private Double longitude;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    private PlaceType type;

    @Column(precision = 2, scale = 1)
    private Double rating;

    @Column(name = "phone_number", length = 20)
    private String phoneNumber;

    @Column(length = 500)
    private String website;

    @Column(name = "opening_hours", columnDefinition = "JSON")
    private String openingHours;

    @Column(name = "image_url", length = 500)
    private String imageUrl;

    @Column(name = "price_range", length = 10)
    private String priceRange;

    @Column(name = "is_user_generated", nullable = false)
    @Builder.Default
    private Boolean isUserGenerated = false;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "created_by")
    private User createdBy;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;
}
