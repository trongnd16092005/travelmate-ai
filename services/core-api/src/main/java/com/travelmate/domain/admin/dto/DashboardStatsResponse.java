package com.travelmate.domain.admin.dto;

import java.util.List;

public record DashboardStatsResponse(
        long totalUsers,
        long activeUsers,
        long totalTrips,
        long totalAIRequests,
        long aiSuccessCount,
        long aiFailCount,
        double aiSuccessRate,
        List<TopDestination> topDestinations
) {
    public record TopDestination(String city, long tripCount) {}
}
