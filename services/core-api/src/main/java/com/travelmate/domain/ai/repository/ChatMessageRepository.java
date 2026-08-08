package com.travelmate.domain.ai.repository;

import com.travelmate.domain.ai.entity.ChatMessage;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ChatMessageRepository extends JpaRepository<ChatMessage, Long> {
    Page<ChatMessage> findAllByConversationIdOrderByCreatedAtAsc(Long convId, Pageable pageable);
    List<ChatMessage> findTop10ByConversationIdOrderByCreatedAtDesc(Long convId);
}
