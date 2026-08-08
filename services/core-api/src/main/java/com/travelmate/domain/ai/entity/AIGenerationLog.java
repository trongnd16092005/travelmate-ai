package com.travelmate.domain.ai.entity;

import com.travelmate.common.enums.AIFeatureType;
import com.travelmate.domain.trip.entity.Trip;
import com.travelmate.domain.user.entity.User;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "ai_generation_logs",
        indexes = {
            @Index(name = "idx_agl_user_id", columnList = "user_id"),
            @Index(name = "idx_agl_feature", columnList = "feature_type")
        })
@Getter @Setter @Builder @NoArgsConstructor @AllArgsConstructor
public class AIGenerationLog {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "trip_id")
    private Trip trip;

    @Enumerated(EnumType.STRING)
    @Column(name = "feature_type", nullable = false, length = 40)
    private AIFeatureType featureType;

    @Column(name = "prompt_summary", length = 500)
    private String promptSummary;

    @Column(name = "input_tokens")
    private Integer inputTokens;

    @Column(name = "output_tokens")
    private Integer outputTokens;

    @Column(name = "duration_ms")
    private Long durationMs;

    @Column(name = "is_success", nullable = false)
    @Builder.Default
    private Boolean isSuccess = true;

    @Column(name = "error_message", columnDefinition = "TEXT")
    private String errorMessage;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;
}
