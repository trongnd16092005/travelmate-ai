package com.travelmate.domain.itinerary.controller;

import com.travelmate.common.response.ApiResponse;
import com.travelmate.domain.itinerary.dto.*;
import com.travelmate.domain.itinerary.service.ItineraryService;
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
@RequestMapping("/api/v1/trips/{tripId}/itinerary")
@RequiredArgsConstructor
@Tag(name = "Itinerary", description = "API quản lý lịch trình")
@SecurityRequirement(name = "bearerAuth")
public class ItineraryController {

    private final ItineraryService itineraryService;
    private final SecurityUtils securityUtils;

    @GetMapping
    @Operation(summary = "Lấy toàn bộ lịch trình")
    public ResponseEntity<ApiResponse<FullItineraryResponse>> getItinerary(@PathVariable Long tripId) {
        return ResponseEntity.ok(ApiResponse.success(
                itineraryService.getFullItinerary(tripId, securityUtils.getCurrentUser())));
    }

    @GetMapping("/days/{dayId}")
    @Operation(summary = "Chi tiết một ngày")
    public ResponseEntity<ApiResponse<ItineraryDayResponse>> getDay(
            @PathVariable Long tripId, @PathVariable Long dayId) {
        return ResponseEntity.ok(ApiResponse.success(
                itineraryService.getDay(tripId, dayId, securityUtils.getCurrentUser())));
    }

    @PutMapping("/days/{dayId}")
    @Operation(summary = "Cập nhật ghi chú ngày")
    public ResponseEntity<ApiResponse<ItineraryDayResponse>> updateDayNote(
            @PathVariable Long tripId, @PathVariable Long dayId,
            @Valid @RequestBody UpdateDayNoteRequest request) {
        return ResponseEntity.ok(ApiResponse.success(
                itineraryService.updateDayNote(tripId, dayId, securityUtils.getCurrentUser(), request)));
    }

    @PostMapping("/days/{dayId}/activities")
    @Operation(summary = "Thêm hoạt động")
    public ResponseEntity<ApiResponse<ActivityResponse>> addActivity(
            @PathVariable Long tripId, @PathVariable Long dayId,
            @Valid @RequestBody ActivityRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.success(
                itineraryService.addActivity(tripId, dayId, securityUtils.getCurrentUser(), request),
                "Đã thêm hoạt động"));
    }

    @PutMapping("/days/{dayId}/activities/{actId}")
    @Operation(summary = "Cập nhật hoạt động")
    public ResponseEntity<ApiResponse<ActivityResponse>> updateActivity(
            @PathVariable Long tripId, @PathVariable Long dayId, @PathVariable Long actId,
            @Valid @RequestBody ActivityRequest request) {
        return ResponseEntity.ok(ApiResponse.success(
                itineraryService.updateActivity(tripId, dayId, actId, securityUtils.getCurrentUser(), request)));
    }

    @PatchMapping("/days/{dayId}/activities/{actId}/status")
    @Operation(summary = "Cập nhật trạng thái hoạt động")
    public ResponseEntity<ApiResponse<ActivityResponse>> updateStatus(
            @PathVariable Long tripId, @PathVariable Long dayId, @PathVariable Long actId,
            @Valid @RequestBody UpdateActivityStatusRequest request) {
        return ResponseEntity.ok(ApiResponse.success(
                itineraryService.updateActivityStatus(tripId, dayId, actId, securityUtils.getCurrentUser(), request)));
    }

    @DeleteMapping("/days/{dayId}/activities/{actId}")
    @Operation(summary = "Xóa hoạt động")
    public ResponseEntity<ApiResponse<Map<String, String>>> deleteActivity(
            @PathVariable Long tripId, @PathVariable Long dayId, @PathVariable Long actId) {
        itineraryService.deleteActivity(tripId, dayId, actId, securityUtils.getCurrentUser());
        return ResponseEntity.ok(ApiResponse.success(Map.of("message", "Đã xóa hoạt động")));
    }

    @PutMapping("/days/{dayId}/activities/reorder")
    @Operation(summary = "Sắp xếp lại hoạt động")
    public ResponseEntity<ApiResponse<List<ActivityResponse>>> reorder(
            @PathVariable Long tripId, @PathVariable Long dayId,
            @Valid @RequestBody ReorderRequest request) {
        return ResponseEntity.ok(ApiResponse.success(
                itineraryService.reorderActivities(tripId, dayId, securityUtils.getCurrentUser(), request)));
    }
}
