package com.travelmate.domain.ai.dto;

import com.travelmate.domain.ai.entity.ChatConversation;
import java.time.LocalDateTime;

public record ConversationResponse(
        Long id,
        String title,
        Long tripId,
        LocalDateTime createdAt,
        LocalDateTime lastMessageAt
) {
    public static ConversationResponse from(ChatConversation c) {
        return new ConversationResponse(
                c.getId(), c.getTitle(),
                c.getTrip() != null ? c.getTrip().getId() : null,
                c.getCreatedAt(), c.getLastMessageAt());
    }
}
