package com.travelmate.domain.place.dto;

import com.travelmate.common.enums.PlaceType;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record CreatePlaceRequest(
        @NotBlank String name,
        String address,
        @NotBlank String city,
        String country,
        Double latitude,
        Double longitude,
        @NotNull PlaceType type,
        String phoneNumber,
        String website,
        String imageUrl,
        String priceRange
) {}
