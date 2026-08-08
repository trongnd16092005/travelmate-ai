package com.travelmate.domain.auth.repository;

import com.travelmate.domain.auth.entity.RefreshToken;
import com.travelmate.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;

import java.util.Optional;

public interface RefreshTokenRepository extends JpaRepository<RefreshToken, Long> {

    Optional<RefreshToken> findByTokenAndIsRevokedFalse(String token);

    @Modifying
    @Query("UPDATE RefreshToken rt SET rt.isRevoked = true WHERE rt.user = :user")
    void revokeAllByUser(User user);

    @Modifying
    @Query("DELETE FROM RefreshToken rt WHERE rt.isRevoked = true OR rt.expiresAt < CURRENT_TIMESTAMP")
    void deleteExpiredTokens();
}
