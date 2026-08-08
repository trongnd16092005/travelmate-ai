package com.travelmate.domain.place.service;

import com.travelmate.common.enums.PlaceType;
import com.travelmate.common.exception.AppException;
import com.travelmate.common.response.PageResponse;
import com.travelmate.domain.place.dto.*;
import com.travelmate.domain.place.entity.Place;
import com.travelmate.domain.place.entity.PlaceReview;
import com.travelmate.domain.place.entity.SavedPlace;
import com.travelmate.domain.place.repository.PlaceRepository;
import com.travelmate.domain.place.repository.PlaceReviewRepository;
import com.travelmate.domain.place.repository.SavedPlaceRepository;
import com.travelmate.domain.trip.entity.Trip;
import com.travelmate.domain.trip.service.TripService;
import com.travelmate.domain.user.entity.User;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional
public class PlaceService {

    private final PlaceRepository placeRepository;
    private final PlaceReviewRepository reviewRepository;
    private final SavedPlaceRepository savedPlaceRepository;
    private final TripService tripService;

    @Transactional(readOnly = true)
    public PageResponse<PlaceResponse> searchPlaces(String keyword, String city,
                                                     String typeStr, int page, int size) {
        PlaceType type = null;
        if (typeStr != null && !typeStr.isBlank()) {
            try { type = PlaceType.valueOf(typeStr.toUpperCase()); } catch (Exception ignored) {}
        }
        var result = placeRepository.searchPlaces(
                keyword == null || keyword.isBlank() ? null : keyword,
                city == null || city.isBlank() ? null : city,
                type, PageRequest.of(page - 1, size));
        return PageResponse.from(result.map(PlaceResponse::from));
    }

    @Transactional(readOnly = true)
    public PlaceResponse getPlace(Long placeId) {
        return PlaceResponse.from(findPlace(placeId));
    }

    public PlaceResponse createPlace(User user, CreatePlaceRequest request) {
        Place place = Place.builder()
                .name(request.name())
                .address(request.address())
                .city(request.city())
                .country(request.country() != null ? request.country() : "Vietnam")
                .latitude(request.latitude())
                .longitude(request.longitude())
                .type(request.type())
                .phoneNumber(request.phoneNumber())
                .website(request.website())
                .imageUrl(request.imageUrl())
                .priceRange(request.priceRange())
                .isUserGenerated(true)
                .createdBy(user)
                .build();
        return PlaceResponse.from(placeRepository.save(place));
    }

    @Transactional(readOnly = true)
    public PageResponse<PlaceReviewResponse> getReviews(Long placeId, int page, int size) {
        findPlace(placeId);
        var result = reviewRepository.findAllByPlaceId(placeId, PageRequest.of(page - 1, size));
        return PageResponse.from(result.map(PlaceReviewResponse::from));
    }

    public PlaceReviewResponse addReview(Long placeId, User user, PlaceReviewRequest request) {
        Place place = findPlace(placeId);
        PlaceReview review = reviewRepository.findByPlaceIdAndUserId(placeId, user.getId())
                .orElse(PlaceReview.builder().place(place).user(user).build());
        review.setRating(request.rating());
        review.setComment(request.comment());
        reviewRepository.save(review);

        // Update average rating
        Double avg = reviewRepository.calculateAverageRating(placeId);
        if (avg != null) {
            place.setRating(Math.round(avg * 10.0) / 10.0);
            placeRepository.save(place);
        }
        return PlaceReviewResponse.from(review);
    }

    @Transactional(readOnly = true)
    public List<PlaceResponse> getSavedPlaces(Long tripId, User user) {
        tripService.getTripAsMember(tripId, user.getId());
        return savedPlaceRepository.findAllByTripId(tripId)
                .stream().map(sp -> PlaceResponse.from(sp.getPlace())).toList();
    }

    public PlaceResponse savePlace(Long tripId, User user, SavePlaceRequest request) {
        Trip trip = tripService.getTripAsEditorOrOwner(tripId, user.getId());
        Place place = findPlace(request.placeId());
        if (savedPlaceRepository.existsByTripIdAndPlaceId(tripId, request.placeId())) {
            throw AppException.conflict("PLACE_ALREADY_SAVED", "Địa điểm đã được lưu");
        }
        SavedPlace saved = SavedPlace.builder().trip(trip).place(place).savedBy(user).build();
        savedPlaceRepository.save(saved);
        return PlaceResponse.from(place);
    }

    public void removeSavedPlace(Long tripId, Long savedId, User user) {
        tripService.getTripAsEditorOrOwner(tripId, user.getId());
        SavedPlace sp = savedPlaceRepository.findById(savedId)
                .orElseThrow(() -> AppException.notFound("SavedPlace"));
        savedPlaceRepository.delete(sp);
    }

    private Place findPlace(Long placeId) {
        return placeRepository.findById(placeId)
                .orElseThrow(() -> AppException.notFound("Place"));
    }
}
