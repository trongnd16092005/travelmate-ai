package com.travelmate.domain.ai.repository;

import com.travelmate.domain.ai.entity.AIGenerationLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

public interface AIGenerationLogRepository extends JpaRepository<AIGenerationLog, Long> {
    long countByIsSuccessTrue();
    long countByIsSuccessFalse();

    @Query("SELECT COUNT(l) FROM AIGenerationLog l WHERE l.user.id = :userId AND l.createdAt >= CURRENT_DATE")
    long countTodayByUser(Long userId);
}
