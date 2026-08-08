package com.travelmate.domain.itinerary.dto;

import jakarta.validation.constraints.NotEmpty;
import java.util.List;

public record ReorderRequest(
        @NotEmpty(message = "Danh sách ID không được rỗng")
        List<Long> orderedActivityIds
) {}
