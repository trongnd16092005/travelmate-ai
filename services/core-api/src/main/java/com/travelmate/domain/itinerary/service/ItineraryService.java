package com.travelmate.domain.itinerary.service;

import com.travelmate.common.exception.AppException;
import com.travelmate.domain.itinerary.dto.*;
import com.travelmate.domain.itinerary.entity.Activity;
import com.travelmate.domain.itinerary.entity.ItineraryDay;
import com.travelmate.domain.itinerary.repository.ActivityRepository;
import com.travelmate.domain.itinerary.repository.ItineraryDayRepository;
import com.travelmate.domain.place.entity.Place;
import com.travelmate.domain.place.repository.PlaceRepository;
import com.travelmate.domain.trip.entity.Trip;
import com.travelmate.domain.trip.service.TripService;
import com.travelmate.domain.user.entity.User;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional
public class ItineraryService {

    private final ItineraryDayRepository dayRepository;
    private final ActivityRepository activityRepository;
    private final PlaceRepository placeRepository;
    private final TripService tripService;

    // ─── GET FULL ITINERARY ────────────────────────────────
    @Transactional(readOnly = true)
    public FullItineraryResponse getFullItinerary(Long tripId, User user) {
        tripService.getTripAsMember(tripId, user.getId());
        List<ItineraryDay> days = dayRepository.findAllByTripIdOrderByDayNumberAsc(tripId);
        List<ItineraryDayResponse> dayResponses = days.stream().map(ItineraryDayResponse::from).toList();
        BigDecimal total = dayResponses.stream()
                .map(ItineraryDayResponse::totalEstimatedCost)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        return new FullItineraryResponse(tripId, dayResponses, total);
    }

    // ─── GET SINGLE DAY ────────────────────────────────────
    @Transactional(readOnly = true)
    public ItineraryDayResponse getDay(Long tripId, Long dayId, User user) {
        tripService.getTripAsMember(tripId, user.getId());
        ItineraryDay day = dayRepository.findByIdAndTripId(dayId, tripId)
                .orElseThrow(() -> AppException.notFound("ItineraryDay"));
        return ItineraryDayResponse.from(day);
    }

    // ─── UPDATE DAY NOTE ───────────────────────────────────
    public ItineraryDayResponse updateDayNote(Long tripId, Long dayId, User user,
                                               UpdateDayNoteRequest request) {
        tripService.getTripAsEditorOrOwner(tripId, user.getId());
        ItineraryDay day = dayRepository.findByIdAndTripId(dayId, tripId)
                .orElseThrow(() -> AppException.notFound("ItineraryDay"));
        day.setNote(request.note());
        dayRepository.save(day);
        return ItineraryDayResponse.from(day);
    }

    // ─── ADD ACTIVITY ──────────────────────────────────────
    public ActivityResponse addActivity(Long tripId, Long dayId, User user, ActivityRequest request) {
        tripService.getTripAsEditorOrOwner(tripId, user.getId());
        ItineraryDay day = dayRepository.findByIdAndTripId(dayId, tripId)
                .orElseThrow(() -> AppException.notFound("ItineraryDay"));

        if (request.startTime() != null && request.endTime() != null
                && request.endTime().isBefore(request.startTime())) {
            throw AppException.badRequest("INVALID_TIME", "Giờ kết thúc phải sau giờ bắt đầu");
        }

        Place place = null;
        if (request.placeId() != null) {
            place = placeRepository.findById(request.placeId()).orElse(null);
        }

        // Determine sort order
        Integer maxOrder = activityRepository.findMaxSortOrder(dayId);
        int sortOrder = request.sortOrder() != null ? request.sortOrder()
                : (maxOrder != null ? maxOrder + 1 : 0);

        Activity activity = Activity.builder()
                .itineraryDay(day)
                .place(place)
                .name(request.name())
                .type(request.type() != null ? request.type() : com.travelmate.common.enums.ActivityType.OTHER)
                .startTime(request.startTime())
                .endTime(request.endTime())
                .estimatedCost(request.estimatedCost())
                .description(request.description())
                .note(request.note())
                .sortOrder(sortOrder)
                .build();
        activityRepository.save(activity);
        return ActivityResponse.from(activity);
    }

    // ─── UPDATE ACTIVITY ───────────────────────────────────
    public ActivityResponse updateActivity(Long tripId, Long dayId, Long actId,
                                            User user, ActivityRequest request) {
        tripService.getTripAsEditorOrOwner(tripId, user.getId());
        dayRepository.findByIdAndTripId(dayId, tripId)
                .orElseThrow(() -> AppException.notFound("ItineraryDay"));

        Activity activity = activityRepository.findById(actId)
                .orElseThrow(() -> AppException.notFound("Activity"));

        if (!activity.getItineraryDay().getId().equals(dayId)) {
            throw AppException.notFound("Activity");
        }

        if (request.name() != null) activity.setName(request.name());
        if (request.type() != null) activity.setType(request.type());
        if (request.startTime() != null) activity.setStartTime(request.startTime());
        if (request.endTime() != null) activity.setEndTime(request.endTime());
        if (request.estimatedCost() != null) activity.setEstimatedCost(request.estimatedCost());
        if (request.description() != null) activity.setDescription(request.description());
        if (request.note() != null) activity.setNote(request.note());
        if (request.placeId() != null) {
            Place place = placeRepository.findById(request.placeId()).orElse(null);
            activity.setPlace(place);
        }
        activityRepository.save(activity);
        return ActivityResponse.from(activity);
    }

    // ─── UPDATE STATUS ─────────────────────────────────────
    public ActivityResponse updateActivityStatus(Long tripId, Long dayId, Long actId,
                                                  User user, UpdateActivityStatusRequest request) {
        tripService.getTripAsEditorOrOwner(tripId, user.getId());
        Activity activity = activityRepository.findById(actId)
                .orElseThrow(() -> AppException.notFound("Activity"));
        activity.setStatus(request.status());
        activityRepository.save(activity);
        return ActivityResponse.from(activity);
    }

    // ─── DELETE ACTIVITY ───────────────────────────────────
    public void deleteActivity(Long tripId, Long dayId, Long actId, User user) {
        tripService.getTripAsEditorOrOwner(tripId, user.getId());
        Activity activity = activityRepository.findById(actId)
                .orElseThrow(() -> AppException.notFound("Activity"));
        if (!activity.getItineraryDay().getId().equals(dayId)) throw AppException.notFound("Activity");
        activityRepository.delete(activity);
    }

    // ─── REORDER ───────────────────────────────────────────
    public List<ActivityResponse> reorderActivities(Long tripId, Long dayId,
                                                     User user, ReorderRequest request) {
        tripService.getTripAsEditorOrOwner(tripId, user.getId());
        dayRepository.findByIdAndTripId(dayId, tripId)
                .orElseThrow(() -> AppException.notFound("ItineraryDay"));

        List<Long> ids = request.orderedActivityIds();
        for (int i = 0; i < ids.size(); i++) {
            activityRepository.updateSortOrder(ids.get(i), i);
        }

        return activityRepository.findAllByItineraryDayIdOrderBySortOrderAsc(dayId)
                .stream().map(ActivityResponse::from).toList();
    }

    // ─── GENERATE DAYS FOR TRIP (called after AI generate) ─
    public void generateDaysForTrip(Trip trip) {
        dayRepository.deleteAllByTripId(trip.getId());
        LocalDate current = trip.getStartDate();
        List<ItineraryDay> days = new ArrayList<>();
        int dayNum = 1;
        while (!current.isAfter(trip.getEndDate())) {
            days.add(ItineraryDay.builder()
                    .trip(trip)
                    .dayNumber(dayNum++)
                    .date(current)
                    .build());
            current = current.plusDays(1);
        }
        dayRepository.saveAll(days);
    }
}
