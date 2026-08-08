package com.travelmate.domain.place.dto;

import jakarta.validation.constraints.NotNull;

public record SavePlaceRequest(@NotNull Long placeId) {}
