package com.travelmate.domain.place.dto;

import com.travelmate.common.enums.PlaceType;
import com.travelmate.domain.place.entity.Place;

public record PlaceResponse(
        Long id, String name, String address, String city, String country,
        Double latitude, Double longitude, PlaceType type,
        Double rating, String phoneNumber, String website,
        String imageUrl, String priceRange, boolean isUserGenerated
) {
    public static PlaceResponse from(Place p) {
        return new PlaceResponse(p.getId(), p.getName(), p.getAddress(), p.getCity(),
                p.getCountry(), p.getLatitude(), p.getLongitude(), p.getType(),
                p.getRating(), p.getPhoneNumber(), p.getWebsite(),
                p.getImageUrl(), p.getPriceRange(),
                Boolean.TRUE.equals(p.getIsUserGenerated()));
    }
}
