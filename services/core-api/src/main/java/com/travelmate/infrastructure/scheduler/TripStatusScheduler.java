package com.travelmate.infrastructure.scheduler;

import com.travelmate.common.enums.TripStatus;
import com.travelmate.domain.trip.entity.Trip;
import com.travelmate.domain.trip.repository.TripRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.PageRequest;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Slf4j
@Component
@RequiredArgsConstructor
public class TripStatusScheduler {

    private final TripRepository tripRepository;

    // Chạy mỗi ngày lúc 00:01 AM – tự động cập nhật trạng thái trip
    @Scheduled(cron = "0 1 0 * * ?")
    @Transactional
    public void updateTripStatuses() {
        try {
            // Get all non-cancelled trips
            List<Trip> trips = tripRepository.findAll().stream()
                    .filter(t -> t.getStatus() != TripStatus.CANCELLED)
                    .toList();

            int updated = 0;
            for (Trip trip : trips) {
                TripStatus oldStatus = trip.getStatus();
                trip.updateStatus();
                if (trip.getStatus() != oldStatus) {
                    tripRepository.save(trip);
                    updated++;
                }
            }
            if (updated > 0) log.info("Updated status for {} trips", updated);
        } catch (Exception e) {
            log.error("Error updating trip statuses: {}", e.getMessage());
        }
    }
}
