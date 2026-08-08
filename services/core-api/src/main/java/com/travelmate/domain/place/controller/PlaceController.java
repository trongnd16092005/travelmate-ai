package com.travelmate.domain.place.controller;

import com.travelmate.common.response.ApiResponse;
import com.travelmate.common.response.PageResponse;
import com.travelmate.domain.place.dto.*;
import com.travelmate.domain.place.service.PlaceService;
import com.travelmate.security.SecurityUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequiredArgsConstructor
@Tag(name = "Places", description = "API quản lý địa điểm")
@SecurityRequirement(name = "bearerAuth")
public class PlaceController {

    private final PlaceService placeService;
    private final SecurityUtils securityUtils;

    @GetMapping("/api/v1/places/search")
    @Operation(summary = "Tìm kiếm địa điểm")
    public ResponseEntity<ApiResponse<PageResponse<PlaceResponse>>> search(
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String city,
            @RequestParam(required = false) String type,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(ApiResponse.success(
                placeService.searchPlaces(keyword, city, type, page, size)));
    }

    @GetMapping("/api/v1/places/{placeId}")
    @Operation(summary = "Chi tiết địa điểm")
    public ResponseEntity<ApiResponse<PlaceResponse>> getPlace(@PathVariable Long placeId) {
        return ResponseEntity.ok(ApiResponse.success(placeService.getPlace(placeId)));
    }

    @PostMapping("/api/v1/places")
    @Operation(summary = "Tạo địa điểm mới (user)")
    public ResponseEntity<ApiResponse<PlaceResponse>> createPlace(
            @Valid @RequestBody CreatePlaceRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.success(
                placeService.createPlace(securityUtils.getCurrentUser(), request)));
    }

    @GetMapping("/api/v1/places/{placeId}/reviews")
    @Operation(summary = "Danh sách đánh giá địa điểm")
    public ResponseEntity<ApiResponse<PageResponse<PlaceReviewResponse>>> getReviews(
            @PathVariable Long placeId,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(ApiResponse.success(placeService.getReviews(placeId, page, size)));
    }

    @PostMapping("/api/v1/places/{placeId}/reviews")
    @Operation(summary = "Viết đánh giá địa điểm")
    public ResponseEntity<ApiResponse<PlaceReviewResponse>> addReview(
            @PathVariable Long placeId, @Valid @RequestBody PlaceReviewRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.success(
                placeService.addReview(placeId, securityUtils.getCurrentUser(), request)));
    }

    // ─── Saved Places (within trip context) ───
    @GetMapping("/api/v1/trips/{tripId}/saved-places")
    @Operation(summary = "Địa điểm đã lưu trong trip")
    public ResponseEntity<ApiResponse<List<PlaceResponse>>> getSaved(@PathVariable Long tripId) {
        return ResponseEntity.ok(ApiResponse.success(
                placeService.getSavedPlaces(tripId, securityUtils.getCurrentUser())));
    }

    @PostMapping("/api/v1/trips/{tripId}/saved-places")
    @Operation(summary = "Lưu địa điểm vào trip")
    public ResponseEntity<ApiResponse<PlaceResponse>> savePlace(
            @PathVariable Long tripId, @Valid @RequestBody SavePlaceRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.success(
                placeService.savePlace(tripId, securityUtils.getCurrentUser(), request)));
    }

    @DeleteMapping("/api/v1/trips/{tripId}/saved-places/{savedId}")
    @Operation(summary = "Xóa địa điểm đã lưu")
    public ResponseEntity<ApiResponse<Map<String, String>>> removePlace(
            @PathVariable Long tripId, @PathVariable Long savedId) {
        placeService.removeSavedPlace(tripId, savedId, securityUtils.getCurrentUser());
        return ResponseEntity.ok(ApiResponse.success(Map.of("message", "Đã xóa khỏi danh sách")));
    }
}
