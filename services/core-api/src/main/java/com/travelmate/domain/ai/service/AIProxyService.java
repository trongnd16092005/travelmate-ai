package com.travelmate.domain.ai.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.travelmate.common.enums.AIFeatureType;
import com.travelmate.common.enums.ActivityType;
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
import com.travelmate.domain.place.entity.Place;
import com.travelmate.domain.place.repository.PlaceRepository;
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

import java.time.Duration;
import java.time.LocalDateTime;
import java.time.LocalTime;
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
    private final PlaceRepository placeRepository;
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
            Map<String, Object> payload = new LinkedHashMap<>();
            payload.put("destination", trip.getDestination());
            payload.put("durationDays", trip.getDurationDays());
            payload.put("startDate", trip.getStartDate().toString());
            payload.put("endDate", trip.getEndDate().toString());
            payload.put("budgetVnd", trip.getBudget() != null ? trip.getBudget().longValue() : 5000000L);
            payload.put("numPeople", trip.getNumPeople());

            List<String> preferences = new ArrayList<>();
            if (request.interests() != null) preferences.addAll(request.interests());
            if (request.travelStyle() != null) preferences.add(request.travelStyle().name());
            else if (trip.getTravelStyle() != null) preferences.add(trip.getTravelStyle().name());
            payload.put("preferences", preferences);
            payload.put("notes", request.specialRequests() != null
                    ? request.specialRequests()
                    : trip.getDescription());

            // Call AI Service
            String responseJson = webClientBuilder.build()
                    .post()
                    .uri(aiEndpoint("/itineraries/generate"))
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
            if (!"ready".equals(root.path("status").asText())) {
                throw new IllegalStateException("AI Service chưa trả về lịch trình hoàn chỉnh");
            }
            JsonNode days = root.path("plan").path("days");
            if (!days.isArray()) {
                throw new IllegalStateException("AI Service trả về plan.days không hợp lệ");
            }

            // Regenerate days
            itineraryService.generateDaysForTrip(trip);
            List<ItineraryDay> itineraryDays = dayRepository
                    .findAllByTripIdOrderByDayNumberAsc(trip.getId());

            if (days.isArray()) {
                for (int i = 0; i < days.size() && i < itineraryDays.size(); i++) {
                    JsonNode dayNode = days.get(i);
                    ItineraryDay day = itineraryDays.get(i);
                    day.setNote(dayNode.path("title").asText(null));
                    dayRepository.save(day);

                    JsonNode activities = dayNode.path("activities");
                    if (activities.isArray()) {
                        int sortOrder = 0;
                        for (JsonNode actNode : activities) {
                            String placeName = nullIfBlank(actNode.path("placeName").asText(null));
                            Place place = findPlace(placeName, trip.getDestination());
                            Activity activity = Activity.builder()
                                    .itineraryDay(day)
                                    .place(place)
                                    .name(actNode.path("title").asText("Hoạt động"))
                                    .type(mapActivityType(actNode.path("kind").asText()))
                                    .description(nullIfBlank(actNode.path("notes").asText(null)))
                                    .note(placeName != null ? "Địa điểm: " + placeName : null)
                                    .startTime(periodStart(actNode.path("period").asText()))
                                    .endTime(periodEnd(actNode.path("period").asText()))
                                    .sortOrder(sortOrder++)
                                    .build();
                            activityRepository.save(activity);
                        }
                    }
                }
            }
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new IllegalStateException("Không thể lưu lịch trình AI", e);
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
        Map<String, Object> tripContext = null;
        if (conversation.getTrip() != null) {
            Trip t = conversation.getTrip();
            tripContext = new LinkedHashMap<>();
            tripContext.put("destination", t.getDestination());
            tripContext.put("startDate", t.getStartDate().toString());
            tripContext.put("endDate", t.getEndDate().toString());
            if (t.getBudget() != null) tripContext.put("budgetVnd", t.getBudget().longValue());
            tripContext.put("numPeople", t.getNumPeople());
        }

        long start = System.currentTimeMillis();
        try {
            // Build payload for FastAPI
            List<Map<String, String>> historyPayload = history.stream()
                    .map(m -> Map.of("role", m.getRole().name().toLowerCase(), "content", m.getContent()))
                    .toList();

            Map<String, Object> payload = new LinkedHashMap<>();
            payload.put("message", request.message());
            payload.put("history", historyPayload);
            if (tripContext != null) payload.put("tripContext", tripContext);

            String responseJson = webClientBuilder.build()
                    .post()
                    .uri(aiEndpoint("/chat"))
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(payload)
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofSeconds(20))
                    .block();

            JsonNode resp = objectMapper.readTree(responseJson);
            String reply = resp.path("reply").asText("Xin lỗi, tôi không thể trả lời lúc này.");
            boolean isOutOfScope = resp.path("isOutOfScope").asBoolean(false);
            List<String> suggestedQuestions = new ArrayList<>();
            JsonNode suggestedNode = resp.path("suggestedQuestions");
            if (suggestedNode.isArray()) {
                suggestedNode.forEach(question -> {
                    if (question.isTextual()) suggestedQuestions.add(question.asText());
                });
            }

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
                    conversation.getId(), aiMsg.getId(), reply, isOutOfScope,
                    suggestedQuestions, aiMsg.getCreatedAt());

        } catch (Exception e) {
            log.warn("AI chat failed: {}", e.getMessage());
            // Fallback response
            return new ChatResponse(conversation.getId(), null,
                    "AI đang khởi động hoặc mất kết nối. Vui lòng thử lại sau.",
                    false, List.of(), LocalDateTime.now());
        }
    }

    // ─── SUGGEST PLACES ────────────────────────────────────
    public String suggestPlaces(User user, SuggestPlacesRequest request) {
        try {
            Map<String, Object> payload = new LinkedHashMap<>();
            payload.put("city", request.city());
            payload.put("type", request.type());
            payload.put("count", request.count() != null ? request.count() : 5);
            payload.put("specialNote", request.specialNote());

            return webClientBuilder.build()
                    .post()
                    .uri(aiEndpoint("/suggest-places"))
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
    private String aiEndpoint(String path) {
        return aiServiceUrl.replaceAll("/+$", "") + path;
    }

    private Place findPlace(String placeName, String destination) {
        if (placeName == null) return null;
        return placeRepository
                .findFirstByNameIgnoreCaseAndCityContainingIgnoreCase(placeName, destination)
                .or(() -> placeRepository.findFirstByNameIgnoreCase(placeName))
                .orElse(null);
    }

    private ActivityType mapActivityType(String kind) {
        return switch (kind) {
            case "visit" -> ActivityType.SIGHTSEEING;
            case "meal" -> ActivityType.FOOD;
            case "travel" -> ActivityType.TRANSPORT;
            default -> ActivityType.OTHER;
        };
    }

    private String nullIfBlank(String value) {
        return value == null || value.isBlank() ? null : value;
    }

    private LocalTime periodStart(String period) {
        return switch (period) {
            case "morning" -> LocalTime.of(8, 0);
            case "afternoon" -> LocalTime.of(14, 0);
            case "evening" -> LocalTime.of(18, 30);
            default -> null;
        };
    }

    private LocalTime periodEnd(String period) {
        return switch (period) {
            case "morning" -> LocalTime.of(11, 0);
            case "afternoon" -> LocalTime.of(17, 0);
            case "evening" -> LocalTime.of(21, 0);
            default -> null;
        };
    }

    // Helper reference for logger in static context
    private static final org.slf4j.Logger Slf4jLogger =
            org.slf4j.LoggerFactory.getLogger(AIProxyService.class);
}
