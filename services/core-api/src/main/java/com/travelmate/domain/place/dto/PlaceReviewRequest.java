package com.travelmate.domain.place.dto;

import jakarta.validation.constraints.*;

public record PlaceReviewRequest(
        @NotNull @Min(1) @Max(5) Integer rating,
        @Size(max = 1000) String comment
) {}
