package com.travelmate.domain.user.service;

import com.travelmate.common.exception.AppException;
import com.travelmate.domain.user.dto.*;
import com.travelmate.domain.user.entity.User;
import com.travelmate.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public UserProfileResponse getProfile(User user) {
        return UserProfileResponse.from(user);
    }

    public UserProfileResponse updateProfile(User user, UpdateProfileRequest request) {
        if (request.fullName() != null) user.setFullName(request.fullName());
        if (request.bio() != null) user.setBio(request.bio());
        if (request.travelStyle() != null) user.setTravelStyle(request.travelStyle());
        userRepository.save(user);
        return UserProfileResponse.from(user);
    }

    public void changePassword(User user, ChangePasswordRequest request) {
        if (!passwordEncoder.matches(request.currentPassword(), user.getPasswordHash())) {
            throw AppException.badRequest("WRONG_PASSWORD", "Mật khẩu hiện tại không đúng");
        }
        user.setPasswordHash(passwordEncoder.encode(request.newPassword()));
        userRepository.save(user);
    }

    public void softDelete(User user) {
        user.setDeletedAt(java.time.LocalDateTime.now());
        userRepository.save(user);
    }
}
