package com.travelmate.domain.trip.service;

import com.travelmate.common.enums.TripRole;
import com.travelmate.common.enums.TripStatus;
import com.travelmate.common.exception.AppException;
import com.travelmate.common.response.PageResponse;
import com.travelmate.domain.trip.dto.*;
import com.travelmate.domain.trip.entity.Trip;
import com.travelmate.domain.trip.entity.TripMember;
import com.travelmate.domain.trip.repository.TripMemberRepository;
import com.travelmate.domain.trip.repository.TripRepository;
import com.travelmate.domain.user.entity.User;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Transactional
public class TripService {

    private final TripRepository tripRepository;
    private final TripMemberRepository tripMemberRepository;

    // ─── LIST ──────────────────────────────────────────────
    @Transactional(readOnly = true)
    public PageResponse<TripSummaryResponse> getMyTrips(User user, String statusStr,
                                                          String keyword, int page, int size) {
        TripStatus status = null;
        if (statusStr != null && !statusStr.isBlank()) {
            try { status = TripStatus.valueOf(statusStr.toUpperCase()); }
            catch (IllegalArgumentException e) { /* ignore invalid status */ }
        }
        Pageable pageable = PageRequest.of(page - 1, size);
        Page<Trip> trips = tripRepository.findAllByMember(user.getId(), status,
                keyword == null || keyword.isBlank() ? null : keyword, pageable);

        Page<TripSummaryResponse> mapped = trips.map(trip -> {
            TripMember myMembership = tripMemberRepository
                    .findByTripIdAndUserId(trip.getId(), user.getId()).orElse(null);
            long memberCount = tripMemberRepository.countByTripId(trip.getId());
            return TripSummaryResponse.from(trip, myMembership, memberCount);
        });
        return PageResponse.from(mapped);
    }

    // ─── GET DETAIL ────────────────────────────────────────
    @Transactional(readOnly = true)
    public TripDetailResponse getTripDetail(Long tripId, User user) {
        Trip trip = getTripAsMember(tripId, user.getId());
        TripMember myMembership = tripMemberRepository
                .findByTripIdAndUserId(tripId, user.getId()).orElse(null);
        List<MemberResponse> members = tripMemberRepository.findAllByTripId(tripId)
                .stream().map(MemberResponse::from).toList();
        return TripDetailResponse.from(trip, myMembership, members);
    }

    @Transactional(readOnly = true)
    public TripDetailResponse getPublicTrip(String publicToken) {
        Trip trip = tripRepository.findByPublicToken(publicToken)
                .orElseThrow(() -> AppException.notFound("Trip"));
        if (!trip.getIsPublic()) throw AppException.forbidden();
        List<MemberResponse> members = tripMemberRepository.findAllByTripId(trip.getId())
                .stream().map(MemberResponse::from).toList();
        return TripDetailResponse.from(trip, null, members);
    }

    // ─── CREATE ────────────────────────────────────────────
    public TripDetailResponse createTrip(User owner, CreateTripRequest request) {
        validateDates(request.startDate(), request.endDate());

        Trip trip = Trip.builder()
                .name(request.name())
                .destination(request.destination())
                .startDate(request.startDate())
                .endDate(request.endDate())
                .budget(request.budget())
                .numPeople(request.numPeople() != null ? request.numPeople() : 1)
                .travelStyle(request.travelStyle())
                .description(request.description())
                .owner(owner)
                .build();
        trip.updateStatus();
        tripRepository.save(trip);

        // Auto-add owner as OWNER member
        TripMember ownerMember = TripMember.builder()
                .trip(trip).user(owner).role(TripRole.OWNER).build();
        tripMemberRepository.save(ownerMember);

        return TripDetailResponse.from(trip, ownerMember, List.of(MemberResponse.from(ownerMember)));
    }

    // ─── UPDATE ────────────────────────────────────────────
    public TripDetailResponse updateTrip(Long tripId, User user, UpdateTripRequest request) {
        Trip trip = getTripAsEditorOrOwner(tripId, user.getId());

        if (request.name() != null) trip.setName(request.name());
        if (request.destination() != null) trip.setDestination(request.destination());
        if (request.travelStyle() != null) trip.setTravelStyle(request.travelStyle());
        if (request.description() != null) trip.setDescription(request.description());
        if (request.budget() != null) trip.setBudget(request.budget());
        if (request.numPeople() != null) trip.setNumPeople(request.numPeople());

        if (request.startDate() != null) trip.setStartDate(request.startDate());
        if (request.endDate() != null) trip.setEndDate(request.endDate());
        if (trip.getStartDate() != null && trip.getEndDate() != null) {
            validateDates(trip.getStartDate(), trip.getEndDate());
        }
        trip.updateStatus();
        tripRepository.save(trip);

        TripMember myMembership = tripMemberRepository.findByTripIdAndUserId(tripId, user.getId()).orElse(null);
        List<MemberResponse> members = tripMemberRepository.findAllByTripId(tripId)
                .stream().map(MemberResponse::from).toList();
        return TripDetailResponse.from(trip, myMembership, members);
    }

    // ─── DELETE ────────────────────────────────────────────
    public void deleteTrip(Long tripId, User user) {
        Trip trip = getTripAsOwner(tripId, user.getId());
        tripRepository.delete(trip);
    }

    // ─── DUPLICATE ─────────────────────────────────────────
    public TripDetailResponse duplicateTrip(Long tripId, User user) {
        Trip original = getTripAsMember(tripId, user.getId());
        LocalDate newStart = LocalDate.now().plusDays(7);
        LocalDate newEnd = newStart.plusDays(original.getDurationDays() - 1);

        CreateTripRequest dupRequest = new CreateTripRequest(
                "[Copy] " + original.getName(), original.getDestination(),
                newStart, newEnd, original.getBudget(),
                original.getNumPeople(), original.getTravelStyle(), original.getDescription());
        return createTrip(user, dupRequest);
    }

    // ─── PUBLIC LINK ───────────────────────────────────────
    public String togglePublicLink(Long tripId, User user, boolean enable) {
        Trip trip = getTripAsOwner(tripId, user.getId());
        if (enable) {
            if (trip.getPublicToken() == null) {
                trip.setPublicToken(UUID.randomUUID().toString().replace("-", "").substring(0, 16));
            }
            trip.setIsPublic(true);
        } else {
            trip.setIsPublic(false);
        }
        tripRepository.save(trip);
        return trip.getIsPublic() ? trip.getPublicToken() : null;
    }

    // ─── HELPERS ───────────────────────────────────────────
    public Trip getTripAsMember(Long tripId, Long userId) {
        return tripRepository.findByIdAndMemberId(tripId, userId)
                .orElseThrow(() -> AppException.notFound("Trip"));
    }

    public Trip getTripAsEditorOrOwner(Long tripId, Long userId) {
        Trip trip = getTripAsMember(tripId, userId);
        TripMember member = tripMemberRepository.findByTripIdAndUserId(tripId, userId)
                .orElseThrow(AppException::forbidden);
        if (!member.canEdit()) throw AppException.forbidden();
        return trip;
    }

    public Trip getTripAsOwner(Long tripId, Long userId) {
        Trip trip = getTripAsMember(tripId, userId);
        TripMember member = tripMemberRepository.findByTripIdAndUserId(tripId, userId)
                .orElseThrow(AppException::forbidden);
        if (!member.isOwner()) throw AppException.forbidden();
        return trip;
    }

    private void validateDates(LocalDate start, LocalDate end) {
        if (end.isBefore(start)) {
            throw AppException.badRequest("INVALID_DATES", "Ngày về phải sau ngày đi");
        }
    }
}
