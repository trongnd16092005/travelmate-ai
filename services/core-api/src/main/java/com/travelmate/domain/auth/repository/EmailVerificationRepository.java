package com.travelmate.domain.auth.repository;

import com.travelmate.domain.auth.entity.EmailVerification;
import com.travelmate.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;

import java.util.Optional;

public interface EmailVerificationRepository extends JpaRepository<EmailVerification, Long> {

    Optional<EmailVerification> findByTokenAndIsUsedFalse(String token);

    @Modifying
    @Query("UPDATE EmailVerification ev SET ev.isUsed = true WHERE ev.user = :user")
    void invalidateAllByUser(User user);
}
