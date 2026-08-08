package com.travelmate.domain.trip.controller;

import com.travelmate.common.response.ApiResponse;
import com.travelmate.domain.trip.dto.*;
import com.travelmate.domain.trip.service.TripMemberService;
import com.travelmate.security.SecurityUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/trips/{tripId}/members")
@RequiredArgsConstructor
@Tag(name = "Trip Members", description = "API quản lý thành viên chuyến đi")
@SecurityRequirement(name = "bearerAuth")
public class TripMemberController {

    private final TripMemberService tripMemberService;
    private final SecurityUtils securityUtils;

    @GetMapping
    @Operation(summary = "Danh sách thành viên")
    public ResponseEntity<ApiResponse<List<MemberResponse>>> getMembers(@PathVariable Long tripId) {
        var user = securityUtils.getCurrentUser();
        return ResponseEntity.ok(ApiResponse.success(tripMemberService.getMembers(tripId, user)));
    }

    @PostMapping("/invite")
    @Operation(summary = "Mời thành viên qua email")
    public ResponseEntity<ApiResponse<InvitationResponse>> inviteMember(
            @PathVariable Long tripId, @Valid @RequestBody InviteMemberRequest request) {
        var user = securityUtils.getCurrentUser();
        return ResponseEntity.ok(ApiResponse.success(
                tripMemberService.inviteMember(tripId, user, request), "Lời mời đã được gửi"));
    }

    @GetMapping("/invitations")
    @Operation(summary = "Danh sách lời mời đang chờ")
    public ResponseEntity<ApiResponse<List<InvitationResponse>>> getPendingInvitations(
            @PathVariable Long tripId) {
        var user = securityUtils.getCurrentUser();
        return ResponseEntity.ok(ApiResponse.success(
                tripMemberService.getPendingInvitations(tripId, user)));
    }

    @PutMapping("/{memberId}/role")
    @Operation(summary = "Thay đổi vai trò thành viên")
    public ResponseEntity<ApiResponse<MemberResponse>> updateRole(
            @PathVariable Long tripId, @PathVariable Long memberId,
            @Valid @RequestBody UpdateMemberRoleRequest request) {
        var user = securityUtils.getCurrentUser();
        return ResponseEntity.ok(ApiResponse.success(
                tripMemberService.updateMemberRole(tripId, memberId, user, request)));
    }

    @DeleteMapping("/{memberId}")
    @Operation(summary = "Xóa thành viên khỏi trip")
    public ResponseEntity<ApiResponse<Map<String, String>>> removeMember(
            @PathVariable Long tripId, @PathVariable Long memberId) {
        var user = securityUtils.getCurrentUser();
        tripMemberService.removeMember(tripId, memberId, user);
        return ResponseEntity.ok(ApiResponse.success(Map.of("message", "Đã xóa thành viên")));
    }

    @DeleteMapping("/me")
    @Operation(summary = "Rời khỏi chuyến đi")
    public ResponseEntity<ApiResponse<Map<String, String>>> leaveTrip(@PathVariable Long tripId) {
        var user = securityUtils.getCurrentUser();
        tripMemberService.leaveTrip(tripId, user);
        return ResponseEntity.ok(ApiResponse.success(Map.of("message", "Đã rời khỏi chuyến đi")));
    }
}
