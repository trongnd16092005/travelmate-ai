package com.travelmate.domain.user.dto;

import com.travelmate.common.enums.TravelStyle;
import jakarta.validation.constraints.Size;

public record UpdateProfileRequest(
        @Size(max = 100, message = "Họ tên tối đa 100 ký tự")
        String fullName,

        @Size(max = 500, message = "Bio tối đa 500 ký tự")
        String bio,

        TravelStyle travelStyle
) {}
