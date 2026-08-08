package com.travelmate.domain.ai.repository;

import com.travelmate.domain.ai.entity.ChatConversation;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ChatConversationRepository extends JpaRepository<ChatConversation, Long> {
    Page<ChatConversation> findAllByUserIdOrderByLastMessageAtDesc(Long userId, Pageable pageable);
}
