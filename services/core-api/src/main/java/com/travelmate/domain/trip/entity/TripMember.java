package com.travelmate.domain.trip.entity;

import com.travelmate.common.enums.TripRole;
import com.travelmate.domain.user.entity.User;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "trip_members",
        uniqueConstraints = @UniqueConstraint(columnNames = {"trip_id", "user_id"}),
        indexes = {
            @Index(name = "idx_tm_trip_id", columnList = "trip_id"),
            @Index(name = "idx_tm_user_id", columnList = "user_id")
        })
@Getter @Setter @Builder @NoArgsConstructor @AllArgsConstructor
public class TripMember {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "trip_id", nullable = false)
    private Trip trip;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private TripRole role;

    @CreationTimestamp
    @Column(name = "joined_at", nullable = false, updatable = false)
    private LocalDateTime joinedAt;

    public boolean isOwner() { return role == TripRole.OWNER; }
    public boolean canEdit() { return role == TripRole.OWNER || role == TripRole.EDITOR; }
}
