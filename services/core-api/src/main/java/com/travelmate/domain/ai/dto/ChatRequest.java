package com.travelmate.domain.ai.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ChatRequest(
        Long conversationId,
        Long tripId,
        @NotBlank(message = "Tin nhắn không được để trống")
        @Size(max = 1000, message = "Tin nhắn tối đa 1000 ký tự")
        String message
) {}
