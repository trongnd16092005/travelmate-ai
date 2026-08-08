package com.travelmate.domain.trip.controller;

import com.travelmate.common.response.ApiResponse;
import com.travelmate.common.response.PageResponse;
import com.travelmate.domain.trip.dto.*;
import com.travelmate.domain.trip.service.TripService;
import com.travelmate.security.SecurityUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/trips")
@RequiredArgsConstructor
@Tag(name = "Trips", description = "API quản lý chuyến đi")
@SecurityRequirement(name = "bearerAuth")
public class TripController {

    private final TripService tripService;
    private final SecurityUtils securityUtils;

    @GetMapping
    @Operation(summary = "Danh sách chuyến đi của tôi")
    public ResponseEntity<ApiResponse<PageResponse<TripSummaryResponse>>> getMyTrips(
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String keyword,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        var user = securityUtils.getCurrentUser();
        return ResponseEntity.ok(ApiResponse.success(
                tripService.getMyTrips(user, status, keyword, page, size)));
    }

    @PostMapping
    @Operation(summary = "Tạo chuyến đi mới")
    public ResponseEntity<ApiResponse<TripDetailResponse>> createTrip(
            @Valid @RequestBody CreateTripRequest request) {
        var user = securityUtils.getCurrentUser();
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success(tripService.createTrip(user, request), "Tạo chuyến đi thành công"));
    }

    @GetMapping("/{tripId}")
    @Operation(summary = "Chi tiết chuyến đi")
    public ResponseEntity<ApiResponse<TripDetailResponse>> getTripDetail(@PathVariable Long tripId) {
        var user = securityUtils.getCurrentUser();
        return ResponseEntity.ok(ApiResponse.success(tripService.getTripDetail(tripId, user)));
    }

    @GetMapping("/public/{publicToken}")
    @Operation(summary = "Xem chuyến đi công khai")
    public ResponseEntity<ApiResponse<TripDetailResponse>> getPublicTrip(@PathVariable String publicToken) {
        return ResponseEntity.ok(ApiResponse.success(tripService.getPublicTrip(publicToken)));
    }

    @PutMapping("/{tripId}")
    @Operation(summary = "Cập nhật chuyến đi")
    public ResponseEntity<ApiResponse<TripDetailResponse>> updateTrip(
            @PathVariable Long tripId, @Valid @RequestBody UpdateTripRequest request) {
        var user = securityUtils.getCurrentUser();
        return ResponseEntity.ok(ApiResponse.success(
                tripService.updateTrip(tripId, user, request), "Cập nhật thành công"));
    }

    @DeleteMapping("/{tripId}")
    @Operation(summary = "Xóa chuyến đi")
    public ResponseEntity<ApiResponse<Map<String, String>>> deleteTrip(@PathVariable Long tripId) {
        var user = securityUtils.getCurrentUser();
        tripService.deleteTrip(tripId, user);
        return ResponseEntity.ok(ApiResponse.success(Map.of("message", "Đã xóa chuyến đi")));
    }

    @PostMapping("/{tripId}/duplicate")
    @Operation(summary = "Nhân bản chuyến đi")
    public ResponseEntity<ApiResponse<TripDetailResponse>> duplicateTrip(@PathVariable Long tripId) {
        var user = securityUtils.getCurrentUser();
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success(tripService.duplicateTrip(tripId, user)));
    }

    @PatchMapping("/{tripId}/public-link")
    @Operation(summary = "Bật/tắt link chia sẻ công khai")
    public ResponseEntity<ApiResponse<Map<String, Object>>> togglePublicLink(
            @PathVariable Long tripId, @RequestParam boolean enable) {
        var user = securityUtils.getCurrentUser();
        String token = tripService.togglePublicLink(tripId, user, enable);
        return ResponseEntity.ok(ApiResponse.success(Map.of(
                "isPublic", enable,
                "publicToken", token != null ? token : ""
        )));
    }
}
