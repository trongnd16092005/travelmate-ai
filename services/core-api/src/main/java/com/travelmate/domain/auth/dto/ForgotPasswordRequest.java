package com.travelmate.domain.auth.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

public record ForgotPasswordRequest(
        @NotBlank @Email(message = "Email không đúng định dạng")
        String email
) {}
