package com.travelmate.domain.ai.dto;

import java.time.LocalDateTime;
import java.util.List;

public record ChatResponse(
        Long conversationId,
        Long messageId,
        String reply,
        boolean isOutOfScope,
        List<String> suggestedQuestions,
        LocalDateTime createdAt
) {}
