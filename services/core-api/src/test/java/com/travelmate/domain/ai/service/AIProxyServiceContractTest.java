package com.travelmate.domain.ai.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import com.travelmate.common.enums.ActivityType;
import com.travelmate.common.enums.TravelStyle;
import com.travelmate.domain.ai.dto.ChatRequest;
import com.travelmate.domain.ai.dto.ChatResponse;
import com.travelmate.domain.ai.dto.GenerateItineraryRequest;
import com.travelmate.domain.ai.dto.SuggestPlacesRequest;
import com.travelmate.domain.ai.entity.ChatConversation;
import com.travelmate.domain.ai.repository.AIGenerationLogRepository;
import com.travelmate.domain.ai.repository.ChatConversationRepository;
import com.travelmate.domain.ai.repository.ChatMessageRepository;
import com.travelmate.domain.itinerary.entity.Activity;
import com.travelmate.domain.itinerary.entity.ItineraryDay;
import com.travelmate.domain.itinerary.repository.ActivityRepository;
import com.travelmate.domain.itinerary.repository.ItineraryDayRepository;
import com.travelmate.domain.itinerary.service.ItineraryService;
import com.travelmate.domain.place.repository.PlaceRepository;
import com.travelmate.domain.trip.entity.Trip;
import com.travelmate.domain.trip.service.TripService;
import com.travelmate.domain.user.entity.User;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.reactive.function.client.WebClient;

import java.io.IOException;
import java.math.BigDecimal;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class AIProxyServiceContractTest {

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final TripService tripService = mock(TripService.class);
    private final ItineraryService itineraryService = mock(ItineraryService.class);
    private final ItineraryDayRepository dayRepository = mock(ItineraryDayRepository.class);
    private final ActivityRepository activityRepository = mock(ActivityRepository.class);
    private final PlaceRepository placeRepository = mock(PlaceRepository.class);
    private final ChatConversationRepository conversationRepository = mock(ChatConversationRepository.class);
    private final ChatMessageRepository messageRepository = mock(ChatMessageRepository.class);
    private final AIGenerationLogRepository logRepository = mock(AIGenerationLogRepository.class);

    private HttpServer server;
    private AIProxyService service;
    private String requestPath;
    private String requestBody;
    private String responseBody;

    @BeforeEach
    void setUp() throws IOException {
        server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/", this::handleRequest);
        server.start();

        service = new AIProxyService(
                WebClient.builder(),
                tripService,
                itineraryService,
                dayRepository,
                activityRepository,
                placeRepository,
                conversationRepository,
                messageRepository,
                logRepository,
                objectMapper
        );
        ReflectionTestUtils.setField(
                service,
                "aiServiceUrl",
                "http://127.0.0.1:" + server.getAddress().getPort() + "/internal/v1/ai/"
        );
    }

    @AfterEach
    void tearDown() {
        server.stop(0);
    }

    @Test
    void suggestPlacesUsesV12PathAndCamelCaseContract() throws Exception {
        responseBody = """
                {"city":"Hà Nội","suggestions":[],"message":null,"provider":"catalog"}
                """;

        String result = service.suggestPlaces(
                User.builder().id(9L).build(),
                new SuggestPlacesRequest("Hà Nội", null, "địa điểm nổi bật", 6)
        );

        assertThat(requestPath).isEqualTo("/internal/v1/ai/suggest-places");
        JsonNode payload = objectMapper.readTree(requestBody);
        assertThat(payload.path("city").asText()).isEqualTo("Hà Nội");
        assertThat(payload.path("specialNote").asText()).isEqualTo("địa điểm nổi bật");
        assertThat(payload.path("count").asInt()).isEqualTo(6);
        assertThat(payload.has("budget")).isFalse();
        assertThat(payload.has("tripId")).isFalse();
        assertThat(result).contains("\"provider\":\"catalog\"");
    }

    @Test
    void generateItineraryPersistsPlanDaysAndMapsActivityKind() throws Exception {
        Trip trip = Trip.builder()
                .id(7L)
                .name("Hà Nội cuối tuần")
                .destination("Hà Nội")
                .startDate(LocalDate.of(2026, 8, 20))
                .endDate(LocalDate.of(2026, 8, 20))
                .budget(BigDecimal.valueOf(5_000_000L))
                .numPeople(2)
                .travelStyle(TravelStyle.RELAXATION)
                .build();
        ItineraryDay day = ItineraryDay.builder().id(21L).trip(trip).dayNumber(1)
                .date(trip.getStartDate()).build();
        when(tripService.getTripAsEditorOrOwner(7L, 9L)).thenReturn(trip);
        when(dayRepository.findAllByTripIdOrderByDayNumberAsc(7L)).thenReturn(List.of(day));
        when(placeRepository.findFirstByNameIgnoreCaseAndCityContainingIgnoreCase(any(), any()))
                .thenReturn(Optional.empty());
        when(placeRepository.findFirstByNameIgnoreCase(any())).thenReturn(Optional.empty());
        responseBody = """
                {
                  "status":"ready",
                  "missingFields":[],
                  "questions":[],
                  "provider":"local",
                  "plan":{
                    "destination":"Hà Nội",
                    "durationDays":1,
                    "numPeople":2,
                    "summary":"Khám phá Hà Nội",
                    "assumptions":[],
                    "budget":{
                      "accommodationVnd":1000000,
                      "foodVnd":1000000,
                      "transportVnd":1000000,
                      "activitiesVnd":1000000,
                      "reserveVnd":1000000,
                      "totalVnd":5000000
                    },
                    "days":[{
                      "day":1,
                      "title":"Ngày phố cổ",
                      "activities":[{
                        "period":"afternoon",
                        "kind":"meal",
                        "title":"Thưởng thức phở",
                        "placeId":"vn-01:pho-co-ha-noi",
                        "placeName":"Phố cổ Hà Nội",
                        "notes":"Chọn quán đông khách địa phương"
                      }]
                    }]
                  }
                }
                """;

        service.generateItinerary(
                User.builder().id(9L).build(),
                new GenerateItineraryRequest(
                        7L,
                        TravelStyle.RELAXATION,
                        List.of("ẩm thực"),
                        "lịch nhẹ"
                )
        );

        assertThat(requestPath).isEqualTo("/internal/v1/ai/itineraries/generate");
        JsonNode payload = objectMapper.readTree(requestBody);
        assertThat(payload.path("durationDays").asInt()).isEqualTo(1);
        assertThat(payload.path("budgetVnd").asLong()).isEqualTo(5_000_000L);
        assertThat(payload.path("numPeople").asInt()).isEqualTo(2);
        assertThat(payload.has("num_days")).isFalse();
        assertThat(payload.has("travelStyle")).isFalse();
        verify(itineraryService).generateDaysForTrip(trip);

        ArgumentCaptor<Activity> activityCaptor = ArgumentCaptor.forClass(Activity.class);
        verify(activityRepository).save(activityCaptor.capture());
        Activity saved = activityCaptor.getValue();
        assertThat(saved.getName()).isEqualTo("Thưởng thức phở");
        assertThat(saved.getType()).isEqualTo(ActivityType.FOOD);
        assertThat(saved.getStartTime()).isEqualTo(LocalTime.of(14, 0));
        assertThat(saved.getEndTime()).isEqualTo(LocalTime.of(17, 0));
        assertThat(saved.getNote()).isEqualTo("Địa điểm: Phố cổ Hà Nội");
    }

    @Test
    void chatForwardsTripContextAndAiMetadata() throws Exception {
        User user = User.builder().id(9L).fullName("Minh").email("minh@example.com").build();
        Trip trip = Trip.builder()
                .id(7L)
                .name("Huế 4 ngày")
                .destination("Huế")
                .startDate(LocalDate.of(2026, 8, 20))
                .endDate(LocalDate.of(2026, 8, 23))
                .budget(BigDecimal.valueOf(8_000_000L))
                .numPeople(2)
                .build();
        ChatConversation conversation = ChatConversation.builder()
                .id(11L)
                .user(user)
                .trip(trip)
                .title("Huế")
                .build();
        when(conversationRepository.findById(11L)).thenReturn(Optional.of(conversation));
        when(messageRepository.findTop10ByConversationIdOrderByCreatedAtDesc(11L))
                .thenReturn(List.of());
        responseBody = """
                {
                  "reply":"Mình chỉ hỗ trợ nội dung du lịch.",
                  "isOutOfScope":true,
                  "suggestedQuestions":["Bạn muốn lên lịch trình tỉnh nào?"],
                  "provider":"local",
                  "modelVersion":"v12",
                  "resetContext":false
                }
                """;

        ChatResponse result = service.chat(user, new ChatRequest(11L, null, "Viết code cho tôi"));

        assertThat(requestPath).isEqualTo("/internal/v1/ai/chat");
        JsonNode payload = objectMapper.readTree(requestBody);
        assertThat(payload.path("history").isArray()).isTrue();
        assertThat(payload.path("tripContext").path("destination").asText()).isEqualTo("Huế");
        assertThat(payload.path("tripContext").path("budgetVnd").asLong()).isEqualTo(8_000_000L);
        assertThat(payload.has("trip_context")).isFalse();
        assertThat(result.isOutOfScope()).isTrue();
        assertThat(result.suggestedQuestions()).containsExactly("Bạn muốn lên lịch trình tỉnh nào?");
    }

    private void handleRequest(HttpExchange exchange) throws IOException {
        requestPath = exchange.getRequestURI().getPath();
        requestBody = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
        byte[] response = responseBody.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
        exchange.sendResponseHeaders(200, response.length);
        exchange.getResponseBody().write(response);
        exchange.close();
    }
}
