package com.travelmate.domain.auth.dto;

import jakarta.validation.constraints.*;

public record ResetPasswordRequest(
        @NotBlank(message = "OTP không được để trống")
        @Size(min = 6, max = 6, message = "OTP phải có đúng 6 ký tự")
        String otp,

        @NotBlank(message = "Email không được để trống")
        @Email
        String email,

        @NotBlank
        @Size(min = 8)
        @Pattern(regexp = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).+$",
                 message = "Mật khẩu phải có ít nhất 1 chữ hoa, 1 chữ thường và 1 số")
        String newPassword
) {}
