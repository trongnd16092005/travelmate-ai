package com.travelmate.domain.trip.dto;

import com.travelmate.common.enums.TravelStyle;
import jakarta.validation.constraints.*;
import java.math.BigDecimal;
import java.time.LocalDate;

public record CreateTripRequest(
        @NotBlank(message = "Tên chuyến đi không được để trống")
        @Size(max = 100, message = "Tên tối đa 100 ký tự")
        String name,

        @NotBlank(message = "Điểm đến không được để trống")
        @Size(max = 255)
        String destination,

        @NotNull(message = "Ngày đi không được để trống")
        LocalDate startDate,

        @NotNull(message = "Ngày về không được để trống")
        LocalDate endDate,

        @Min(value = 0, message = "Ngân sách phải >= 0")
        BigDecimal budget,

        @Min(value = 1) @Max(value = 100)
        Integer numPeople,

        TravelStyle travelStyle,

        @Size(max = 2000)
        String description
) {}
