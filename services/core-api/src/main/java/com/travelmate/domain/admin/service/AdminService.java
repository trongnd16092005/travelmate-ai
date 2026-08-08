package com.travelmate.domain.admin.service;

import com.travelmate.common.enums.AccountStatus;
import com.travelmate.common.exception.AppException;
import com.travelmate.common.response.PageResponse;
import com.travelmate.domain.admin.dto.*;
import com.travelmate.domain.ai.repository.AIGenerationLogRepository;
import com.travelmate.domain.auth.repository.RefreshTokenRepository;
import com.travelmate.domain.trip.repository.TripRepository;
import com.travelmate.domain.user.entity.User;
import com.travelmate.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional
public class AdminService {

    private final UserRepository userRepository;
    private final TripRepository tripRepository;
    private final AIGenerationLogRepository aiLogRepository;
    private final RefreshTokenRepository refreshTokenRepository;

    @Transactional(readOnly = true)
    public PageResponse<AdminUserResponse> getUsers(String keyword, String statusStr,
                                                     int page, int size) {
        AccountStatus status = null;
        if (statusStr != null && !statusStr.isBlank()) {
            try { status = AccountStatus.valueOf(statusStr.toUpperCase()); } catch (Exception ignored) {}
        }
        Page<User> users = userRepository.findAllActiveUsers(status, keyword,
                PageRequest.of(page - 1, size));
        return PageResponse.from(users.map(AdminUserResponse::from));
    }

    @Transactional(readOnly = true)
    public AdminUserResponse getUser(Long userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> AppException.notFound("User"));
        return AdminUserResponse.from(user);
    }

    public AdminUserResponse updateUserStatus(Long userId, UpdateUserStatusRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> AppException.notFound("User"));

        user.setStatus(request.status());

        // If locking, revoke all tokens
        if (request.status() == AccountStatus.LOCKED) {
            refreshTokenRepository.revokeAllByUser(user);
        }

        userRepository.save(user);
        return AdminUserResponse.from(user);
    }

    public void deleteUser(Long userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> AppException.notFound("User"));
        user.setDeletedAt(LocalDateTime.now());
        user.setStatus(AccountStatus.DELETED);
        refreshTokenRepository.revokeAllByUser(user);
        userRepository.save(user);
    }

    @Transactional(readOnly = true)
    public DashboardStatsResponse getDashboardStats() {
        long totalUsers = userRepository.count();
        long activeUsers = userRepository.findAllActiveUsers(
                AccountStatus.ACTIVE, null, PageRequest.of(0, 1)).getTotalElements();
        long totalTrips = tripRepository.count();
        long aiSuccess = aiLogRepository.countByIsSuccessTrue();
        long aiFail = aiLogRepository.countByIsSuccessFalse();
        long totalAI = aiSuccess + aiFail;
        double successRate = totalAI > 0 ? (double) aiSuccess / totalAI * 100 : 0.0;

        // Top destinations from trips
        List<DashboardStatsResponse.TopDestination> topDests = List.of();

        return new DashboardStatsResponse(
                totalUsers, activeUsers, totalTrips,
                totalAI, aiSuccess, aiFail,
                Math.round(successRate * 10.0) / 10.0,
                topDests);
    }
}
