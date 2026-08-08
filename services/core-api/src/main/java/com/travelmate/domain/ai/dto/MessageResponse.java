package com.travelmate.domain.ai.dto;

import com.travelmate.common.enums.MessageRole;
import com.travelmate.domain.ai.entity.ChatMessage;
import java.time.LocalDateTime;

public record MessageResponse(
        Long id,
        MessageRole role,
        String content,
        LocalDateTime createdAt
) {
    public static MessageResponse from(ChatMessage m) {
        return new MessageResponse(m.getId(), m.getRole(), m.getContent(), m.getCreatedAt());
    }
}
