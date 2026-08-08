package com.travelmate.domain.ai.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.travelmate.common.enums.AIFeatureType;
import com.travelmate.common.enums.MessageRole;
import com.travelmate.common.exception.AppException;
import com.travelmate.domain.ai.dto.*;
import com.travelmate.domain.ai.entity.AIGenerationLog;
import com.travelmate.domain.ai.entity.ChatConversation;
import com.travelmate.domain.ai.entity.ChatMessage;
import com.travelmate.domain.ai.repository.AIGenerationLogRepository;
import com.travelmate.domain.ai.repository.ChatConversationRepository;
import com.travelmate.domain.ai.repository.ChatMessageRepository;
import com.travelmate.domain.itinerary.entity.Activity;
import com.travelmate.domain.itinerary.entity.ItineraryDay;
import com.travelmate.domain.itinerary.repository.ActivityRepository;
import com.travelmate.domain.itinerary.repository.ItineraryDayRepository;
import com.travelmate.domain.itinerary.service.ItineraryService;
import com.travelmate.domain.trip.entity.Trip;
import com.travelmate.domain.trip.service.TripService;
import com.travelmate.domain.user.entity.User;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.math.BigDecimal;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.format.DateTimeParseException;
import java.util.*;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class AIProxyService {

    private final WebClient.Builder webClientBuilder;
    private final TripService tripService;
    private final ItineraryService itineraryService;
    private final ItineraryDayRepository dayRepository;
    private final ActivityRepository activityRepository;
    private final ChatConversationRepository conversationRepository;
    private final ChatMessageRepository messageRepository;
    private final AIGenerationLogRepository logRepository;
    private final ObjectMapper objectMapper;

    @Value("${app.ai-service-url}")
    private String aiServiceUrl;

    // ─── GENERATE ITINERARY ────────────────────────────────
    public String generateItinerary(User user, GenerateItineraryRequest request) {
        Trip trip = tripService.getTripAsEditorOrOwner(request.tripId(), user.getId());
        long start = System.currentTimeMillis();
        AIGenerationLog log = AIGenerationLog.builder()
                .user(user).trip(trip)
                .featureType(AIFeatureType.GENERATE_ITINERARY)
                .promptSummary("Generate itinerary for: " + trip.getDestination())
                .build();

        try {
            // Build request payload for FastAPI
            Map<String, Object> payload = new HashMap<>();
            payload.put("destination", trip.getDestination());
            payload.put("num_days", trip.getDurationDays());
            payload.put("start_date", trip.getStartDate().toString());
            payload.put("end_date", trip.getEndDate().toString());
            payload.put("budget", trip.getBudget() != null ? trip.getBudget().longValue() : 5000000L);
            payload.put("num_people", trip.getNumPeople());
            payload.put("travel_style", request.travelStyle() != null ?
                    request.travelStyle().name() : (trip.getTravelStyle() != null ?
                    trip.getTravelStyle().name() : "RELAXATION"));
            payload.put("interests", request.interests() != null ? request.interests() : List.of());
            payload.put("special_requests", request.specialRequests() != null ?
                    request.specialRequests() : "");

            // Call AI Service
            String responseJson = webClientBuilder.build()
                    .post()
                    .uri(aiServiceUrl + "/generate-itinerary")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(payload)
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofSeconds(30))
                    .block();

            // Parse and save itinerary
            saveGeneratedItinerary(trip, responseJson);

            log.setIsSuccess(true);
            log.setDurationMs(System.currentTimeMillis() - start);
            logRepository.save(log);

            return responseJson;

        } catch (WebClientResponseException e) {
            log.setIsSuccess(false);
            log.setErrorMessage(e.getMessage());
            logRepository.save(log);
            throw AppException.badRequest("AI_SERVICE_ERROR",
                    "AI Service trả về lỗi: " + e.getStatusCode());
        } catch (Exception e) {
            log.setIsSuccess(false);
            log.setErrorMessage(e.getMessage());
            logRepository.save(log);
            Slf4jLogger.warn("AI generate itinerary failed: {}", e.getMessage());
            throw new AppException("AI_SERVICE_UNAVAILABLE",
                    "AI đang tạm thời không khả dụng, vui lòng thử lại sau",
                    HttpStatus.SERVICE_UNAVAILABLE);
        }
    }

    private void saveGeneratedItinerary(Trip trip, String responseJson) {
        try {
            JsonNode root = objectMapper.readTree(responseJson);
            JsonNode days = root.path("days");

            // Regenerate days
            itineraryService.generateDaysForTrip(trip);
            List<ItineraryDay> itineraryDays = dayRepository
                    .findAllByTripIdOrderByDayNumberAsc(trip.getId());

            if (days.isArray()) {
                for (int i = 0; i < days.size() && i < itineraryDays.size(); i++) {
                    JsonNode dayNode = days.get(i);
                    ItineraryDay day = itineraryDays.get(i);
                    day.setNote(dayNode.path("theme").asText(null));
                    dayRepository.save(day);

                    JsonNode activities = dayNode.path("activities");
                    if (activities.isArray()) {
                        int sortOrder = 0;
                        for (JsonNode actNode : activities) {
                            Activity activity = Activity.builder()
                                    .itineraryDay(day)
                                    .name(actNode.path("name").asText("Hoạt động"))
                                    .description(actNode.path("description").asText(null))
                                    .note(actNode.path("bookingNote").asText(null))
                                    .estimatedCost(parseDecimal(actNode.path("estimatedCost").asText(null)))
                                    .startTime(parseTime(actNode.path("startTime").asText(null)))
                                    .endTime(parseTime(actNode.path("endTime").asText(null)))
                                    .sortOrder(sortOrder++)
                                    .build();
                            activityRepository.save(activity);
                        }
                    }
                }
            }
        } catch (Exception e) {
            log.warn("Could not save AI itinerary to DB: {}", e.getMessage());
        }
    }

    // ─── CHAT ──────────────────────────────────────────────
    public ChatResponse chat(User user, ChatRequest request) {
        // Get or create conversation
        ChatConversation conversation;
        if (request.conversationId() != null) {
            conversation = conversationRepository.findById(request.conversationId())
                    .orElseThrow(() -> AppException.notFound("Conversation"));
            if (!conversation.getUser().getId().equals(user.getId())) throw AppException.forbidden();
        } else {
            Trip trip = null;
            if (request.tripId() != null) {
                try { trip = tripService.getTripAsMember(request.tripId(), user.getId()); }
                catch (Exception ignored) {}
            }
            conversation = ChatConversation.builder()
                    .user(user).trip(trip)
                    .title(request.message().length() > 50 ?
                            request.message().substring(0, 50) + "..." : request.message())
                    .build();
            conversationRepository.save(conversation);
        }

        // Get recent messages for context
        List<ChatMessage> history = messageRepository
                .findTop10ByConversationIdOrderByCreatedAtDesc(conversation.getId());
        Collections.reverse(history);

        // Build trip context
        String tripContext = "";
        if (conversation.getTrip() != null) {
            Trip t = conversation.getTrip();
            tripContext = String.format(
                    "Chuyến đi: %s, điểm đến: %s, từ %s đến %s, %d ngày, ngân sách: %s VND",
                    t.getName(), t.getDestination(),
                    t.getStartDate(), t.getEndDate(),
                    t.getDurationDays(),
                    t.getBudget() != null ? t.getBudget().toPlainString() : "chưa xác định");
        }

        long start = System.currentTimeMillis();
        try {
            // Build payload for FastAPI
            List<Map<String, String>> historyPayload = history.stream()
                    .map(m -> Map.of("role", m.getRole().name().toLowerCase(), "content", m.getContent()))
                    .toList();

            Map<String, Object> payload = new HashMap<>();
            payload.put("message", request.message());
            payload.put("trip_context", tripContext);
            payload.put("chat_history", historyPayload);

            String responseJson = webClientBuilder.build()
                    .post()
                    .uri(aiServiceUrl + "/chat")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(payload)
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofSeconds(20))
                    .block();

            JsonNode resp = objectMapper.readTree(responseJson);
            String reply = resp.path("reply").asText("Xin lỗi, tôi không thể trả lời lúc này.");

            // Save messages
            ChatMessage userMsg = ChatMessage.builder()
                    .conversation(conversation).role(MessageRole.USER)
                    .content(request.message()).build();
            messageRepository.save(userMsg);

            ChatMessage aiMsg = ChatMessage.builder()
                    .conversation(conversation).role(MessageRole.ASSISTANT)
                    .content(reply).build();
            messageRepository.save(aiMsg);

            conversation.setLastMessageAt(LocalDateTime.now());
            conversationRepository.save(conversation);

            // Log
            logRepository.save(AIGenerationLog.builder()
                    .user(user).featureType(AIFeatureType.CHAT)
                    .isSuccess(true).durationMs(System.currentTimeMillis() - start)
                    .build());

            return new ChatResponse(
                    conversation.getId(), aiMsg.getId(), reply, false,
                    List.of(), aiMsg.getCreatedAt());

        } catch (Exception e) {
            log.warn("AI chat failed: {}", e.getMessage());
            // Fallback response
            return new ChatResponse(conversation.getId(), null,
                    "Xin lỗi, AI đang tạm thời không khả dụng. Vui lòng thử lại sau! 🙏",
                    false, List.of(), LocalDateTime.now());
        }
    }

    // ─── SUGGEST PLACES ────────────────────────────────────
    public String suggestPlaces(User user, SuggestPlacesRequest request) {
        try {
            Map<String, Object> payload = new HashMap<>();
            payload.put("city", request.city());
            payload.put("type", request.type());
            payload.put("budget", request.budget());
            payload.put("count", request.count() > 0 ? request.count() : 5);
            payload.put("special_note", request.specialNote());

            return webClientBuilder.build()
                    .post()
                    .uri(aiServiceUrl + "/suggest-places")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(payload)
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofSeconds(20))
                    .block();
        } catch (Exception e) {
            log.warn("AI suggest places failed: {}", e.getMessage());
            throw new AppException("AI_SERVICE_UNAVAILABLE",
                    "Không thể lấy gợi ý lúc này", HttpStatus.SERVICE_UNAVAILABLE);
        }
    }

    // ─── OPTIMIZE ──────────────────────────────────────────
    public String optimizeItinerary(User user, Long tripId) {
        Trip trip = tripService.getTripAsEditorOrOwner(tripId, user.getId());
        List<ItineraryDay> days = dayRepository.findAllByTripIdOrderByDayNumberAsc(tripId);

        try {
            Map<String, Object> payload = new HashMap<>();
            payload.put("trip_name", trip.getName());
            payload.put("destination", trip.getDestination());
            payload.put("days", days.stream().map(d -> {
                Map<String, Object> dayMap = new HashMap<>();
                dayMap.put("day_number", d.getDayNumber());
                dayMap.put("date", d.getDate().toString());
                dayMap.put("activities", d.getActivities().stream().map(a -> {
                    Map<String, Object> actMap = new HashMap<>();
                    actMap.put("id", a.getId());
                    actMap.put("name", a.getName());
                    actMap.put("type", a.getType().name());
                    actMap.put("start_time", a.getStartTime() != null ? a.getStartTime().toString() : null);
                    actMap.put("place_name", a.getPlace() != null ? a.getPlace().getName() : null);
                    return actMap;
                }).toList());
                return dayMap;
            }).toList());

            return webClientBuilder.build()
                    .post()
                    .uri(aiServiceUrl + "/optimize-itinerary")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(payload)
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofSeconds(25))
                    .block();
        } catch (Exception e) {
            log.warn("AI optimize failed: {}", e.getMessage());
            throw new AppException("AI_SERVICE_UNAVAILABLE",
                    "Không thể tối ưu lịch trình lúc này", HttpStatus.SERVICE_UNAVAILABLE);
        }
    }

    // ─── CONVERSATION HELPERS ──────────────────────────────
    @Transactional(readOnly = true)
    public List<ConversationResponse> getConversations(User user, int page, int size) {
        return conversationRepository
                .findAllByUserIdOrderByLastMessageAtDesc(
                        user.getId(),
                        org.springframework.data.domain.PageRequest.of(page - 1, size))
                .stream().map(ConversationResponse::from).toList();
    }

    @Transactional(readOnly = true)
    public List<MessageResponse> getMessages(User user, Long convId, int page, int size) {
        ChatConversation conv = conversationRepository.findById(convId)
                .orElseThrow(() -> AppException.notFound("Conversation"));
        if (!conv.getUser().getId().equals(user.getId())) throw AppException.forbidden();
        return messageRepository
                .findAllByConversationIdOrderByCreatedAtAsc(
                        convId, org.springframework.data.domain.PageRequest.of(page - 1, size))
                .stream().map(MessageResponse::from).toList();
    }

    public void deleteConversation(User user, Long convId) {
        ChatConversation conv = conversationRepository.findById(convId)
                .orElseThrow(() -> AppException.notFound("Conversation"));
        if (!conv.getUser().getId().equals(user.getId())) throw AppException.forbidden();
        conversationRepository.delete(conv);
    }

    // ─── UTILS ─────────────────────────────────────────────
    private BigDecimal parseDecimal(String value) {
        if (value == null || value.isBlank()) return null;
        try { return new BigDecimal(value.replaceAll("[^0-9.]", "")); }
        catch (Exception e) { return null; }
    }

    private LocalTime parseTime(String value) {
        if (value == null || value.isBlank()) return null;
        try { return LocalTime.parse(value); }
        catch (DateTimeParseException e) { return null; }
    }

    // Helper reference for logger in static context
    private static final org.slf4j.Logger Slf4jLogger =
            org.slf4j.LoggerFactory.getLogger(AIProxyService.class);
}
