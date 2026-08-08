package com.travelmate.domain.user.repository;

import com.travelmate.common.enums.AccountStatus;
import com.travelmate.domain.user.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Long> {

    Optional<User> findByEmailAndDeletedAtIsNull(String email);

    Optional<User> findByGoogleIdAndDeletedAtIsNull(String googleId);

    boolean existsByEmailAndDeletedAtIsNull(String email);

    @Query("SELECT u FROM User u WHERE u.deletedAt IS NULL " +
           "AND (:status IS NULL OR u.status = :status) " +
           "AND (:keyword IS NULL OR LOWER(u.fullName) LIKE LOWER(CONCAT('%',:keyword,'%')) " +
           "OR LOWER(u.email) LIKE LOWER(CONCAT('%',:keyword,'%')))")
    Page<User> findAllActiveUsers(@Param("status") AccountStatus status,
                                  @Param("keyword") String keyword,
                                  Pageable pageable);
}
