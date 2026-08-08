package com.travelmate.domain.trip.controller;

import com.travelmate.common.response.ApiResponse;
import com.travelmate.domain.trip.service.TripMemberService;
import com.travelmate.security.SecurityUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/invitations")
@RequiredArgsConstructor
@Tag(name = "Invitations", description = "API xử lý lời mời")
public class InvitationController {

    private final TripMemberService tripMemberService;
    private final SecurityUtils securityUtils;

    @GetMapping("/accept")
    @Operation(summary = "Chấp nhận lời mời tham gia trip")
    @SecurityRequirement(name = "bearerAuth")
    public ResponseEntity<ApiResponse<Map<String, String>>> acceptInvitation(
            @RequestParam String token) {
        var user = securityUtils.getCurrentUser();
        tripMemberService.acceptInvitation(token, user);
        return ResponseEntity.ok(ApiResponse.success(
                Map.of("message", "Tham gia chuyến đi thành công!")));
    }
}
