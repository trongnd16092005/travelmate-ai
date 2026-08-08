package com.travelmate.infrastructure.scheduler;

import com.travelmate.domain.auth.repository.RefreshTokenRepository;
import com.travelmate.domain.trip.repository.InvitationRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Component
@RequiredArgsConstructor
public class CleanupScheduler {

    private final RefreshTokenRepository refreshTokenRepository;
    private final InvitationRepository invitationRepository;

    // Chạy mỗi ngày lúc 2:00 AM
    @Scheduled(cron = "0 0 2 * * ?")
    @Transactional
    public void cleanupExpiredTokens() {
        int deleted = 0;
        try {
            refreshTokenRepository.deleteExpiredTokens();
            log.info("Cleaned up expired refresh tokens");
        } catch (Exception e) {
            log.error("Error cleaning up refresh tokens: {}", e.getMessage());
        }
    }

    // Chạy mỗi giờ
    @Scheduled(cron = "0 0 * * * ?")
    @Transactional
    public void expireStaleInvitations() {
        try {
            int expired = invitationRepository.expireStaleInvitations();
            if (expired > 0) {
                log.info("Expired {} stale invitations", expired);
            }
        } catch (Exception e) {
            log.error("Error expiring invitations: {}", e.getMessage());
        }
    }
}
