package com.travelmate.domain.ai.controller;

import com.travelmate.common.response.ApiResponse;
import com.travelmate.domain.ai.dto.*;
import com.travelmate.domain.ai.service.AIProxyService;
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
@RequestMapping("/api/v1/ai")
@RequiredArgsConstructor
@Tag(name = "AI Features", description = "API tính năng AI")
@SecurityRequirement(name = "bearerAuth")
public class AIController {

    private final AIProxyService aiProxyService;
    private final SecurityUtils securityUtils;

    @PostMapping("/generate-itinerary")
    @Operation(summary = "AI sinh lịch trình tự động")
    public ResponseEntity<ApiResponse<Object>> generateItinerary(
            @Valid @RequestBody GenerateItineraryRequest request) {
        var user = securityUtils.getCurrentUser();
        String result = aiProxyService.generateItinerary(user, request);
        return ResponseEntity.ok(ApiResponse.success(result, "Lịch trình đã được tạo thành công!"));
    }

    @PostMapping("/chat")
    @Operation(summary = "Chat với AI chatbot")
    public ResponseEntity<ApiResponse<ChatResponse>> chat(
            @Valid @RequestBody ChatRequest request) {
        var user = securityUtils.getCurrentUser();
        return ResponseEntity.ok(ApiResponse.success(aiProxyService.chat(user, request)));
    }

    @PostMapping("/suggest-places")
    @Operation(summary = "AI gợi ý địa điểm")
    public ResponseEntity<ApiResponse<Object>> suggestPlaces(
            @Valid @RequestBody SuggestPlacesRequest request) {
        var user = securityUtils.getCurrentUser();
        String result = aiProxyService.suggestPlaces(user, request);
        return ResponseEntity.ok(ApiResponse.success(result));
    }

    @PostMapping("/optimize-itinerary/{tripId}")
    @Operation(summary = "AI tối ưu lịch trình")
    public ResponseEntity<ApiResponse<Object>> optimizeItinerary(@PathVariable Long tripId) {
        var user = securityUtils.getCurrentUser();
        String result = aiProxyService.optimizeItinerary(user, tripId);
        return ResponseEntity.ok(ApiResponse.success(result));
    }

    @GetMapping("/conversations")
    @Operation(summary = "Danh sách cuộc hội thoại")
    public ResponseEntity<ApiResponse<List<ConversationResponse>>> getConversations(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {
        var user = securityUtils.getCurrentUser();
        return ResponseEntity.ok(ApiResponse.success(
                aiProxyService.getConversations(user, page, size)));
    }

    @GetMapping("/conversations/{convId}/messages")
    @Operation(summary = "Lịch sử chat")
    public ResponseEntity<ApiResponse<List<MessageResponse>>> getMessages(
            @PathVariable Long convId,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "50") int size) {
        var user = securityUtils.getCurrentUser();
        return ResponseEntity.ok(ApiResponse.success(
                aiProxyService.getMessages(user, convId, page, size)));
    }

    @DeleteMapping("/conversations/{convId}")
    @Operation(summary = "Xóa cuộc hội thoại")
    public ResponseEntity<ApiResponse<Map<String, String>>> deleteConversation(
            @PathVariable Long convId) {
        var user = securityUtils.getCurrentUser();
        aiProxyService.deleteConversation(user, convId);
        return ResponseEntity.ok(ApiResponse.success(Map.of("message", "Đã xóa cuộc hội thoại")));
    }
}
