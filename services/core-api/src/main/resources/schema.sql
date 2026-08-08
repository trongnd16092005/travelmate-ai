-- =============================================
-- TravelMate AI – Database Schema
-- MySQL 8.x | Charset: utf8mb4
-- =============================================

CREATE DATABASE IF NOT EXISTS travelmate_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE travelmate_db;

-- ─────────────── USERS ───────────────
CREATE TABLE users (
    id                    BIGINT AUTO_INCREMENT PRIMARY KEY,
    full_name             VARCHAR(100)  NOT NULL,
    email                 VARCHAR(255)  NOT NULL,
    password_hash         VARCHAR(255)  NULL,
    avatar_url            VARCHAR(500)  NULL,
    role                  ENUM('ADMIN','USER') NOT NULL DEFAULT 'USER',
    status                ENUM('PENDING','ACTIVE','LOCKED','DELETED') NOT NULL DEFAULT 'PENDING',
    google_id             VARCHAR(255)  NULL,
    email_verified_at     DATETIME      NULL,
    failed_login_attempts INT           NOT NULL DEFAULT 0,
    locked_until          DATETIME      NULL,
    travel_style          ENUM('ADVENTURE','RELAXATION','CULTURE','FOOD_TOUR','FAMILY','BUDGET') NULL,
    bio                   VARCHAR(500)  NULL,
    created_at            DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at            DATETIME      NULL,
    UNIQUE KEY uq_users_email (email),
    UNIQUE KEY uq_users_google_id (google_id),
    INDEX idx_users_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────── EMAIL VERIFICATIONS ───────────────
CREATE TABLE email_verifications (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id    BIGINT       NOT NULL,
    token      VARCHAR(512) NOT NULL,
    expires_at DATETIME     NOT NULL,
    is_used    TINYINT(1)   NOT NULL DEFAULT 0,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_ev_token (token),
    FOREIGN KEY fk_ev_user (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────── REFRESH TOKENS ───────────────
CREATE TABLE refresh_tokens (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id      BIGINT       NOT NULL,
    token        VARCHAR(512) NOT NULL,
    expires_at   DATETIME     NOT NULL,
    is_revoked   TINYINT(1)   NOT NULL DEFAULT 0,
    device_info  VARCHAR(255) NULL,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at DATETIME     NULL,
    UNIQUE KEY uq_rt_token (token),
    INDEX idx_rt_user_id (user_id),
    FOREIGN KEY fk_rt_user (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────── TRIPS ───────────────
CREATE TABLE trips (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(100)  NOT NULL,
    destination    VARCHAR(255)  NOT NULL,
    cover_image_url VARCHAR(500) NULL,
    start_date     DATE          NOT NULL,
    end_date       DATE          NOT NULL,
    budget         DECIMAL(15,2) NULL,
    num_people     INT           NOT NULL DEFAULT 1,
    travel_style   ENUM('ADVENTURE','RELAXATION','CULTURE','FOOD_TOUR','FAMILY','BUDGET') NULL,
    description    TEXT          NULL,
    status         ENUM('UPCOMING','ONGOING','COMPLETED','CANCELLED') NOT NULL DEFAULT 'UPCOMING',
    owner_id       BIGINT        NOT NULL,
    is_public      TINYINT(1)    NOT NULL DEFAULT 0,
    public_token   VARCHAR(64)   NULL,
    created_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_trips_public_token (public_token),
    INDEX idx_trips_owner_id (owner_id),
    INDEX idx_trips_status (status),
    INDEX idx_trips_destination (destination),
    FOREIGN KEY fk_trips_owner (owner_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────── TRIP MEMBERS ───────────────
CREATE TABLE trip_members (
    id        BIGINT AUTO_INCREMENT PRIMARY KEY,
    trip_id   BIGINT NOT NULL,
    user_id   BIGINT NOT NULL,
    role      ENUM('OWNER','EDITOR','VIEWER') NOT NULL,
    joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_tm_trip_user (trip_id, user_id),
    INDEX idx_tm_trip_id (trip_id),
    INDEX idx_tm_user_id (user_id),
    FOREIGN KEY fk_tm_trip (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    FOREIGN KEY fk_tm_user (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────── INVITATIONS ───────────────
CREATE TABLE invitations (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    trip_id       BIGINT       NOT NULL,
    inviter_id    BIGINT       NOT NULL,
    invitee_email VARCHAR(255) NOT NULL,
    invitee_id    BIGINT       NULL,
    role          ENUM('EDITOR','VIEWER') NOT NULL DEFAULT 'VIEWER',
    status        ENUM('PENDING','ACCEPTED','DECLINED','EXPIRED') NOT NULL DEFAULT 'PENDING',
    token         VARCHAR(255) NOT NULL,
    expires_at    DATETIME     NOT NULL,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_inv_token (token),
    INDEX idx_inv_trip_id (trip_id),
    FOREIGN KEY fk_inv_trip (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    FOREIGN KEY fk_inv_inviter (inviter_id) REFERENCES users(id),
    FOREIGN KEY fk_inv_invitee (invitee_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────── ITINERARY DAYS ───────────────
CREATE TABLE itinerary_days (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    trip_id    BIGINT NOT NULL,
    day_number INT    NOT NULL,
    date       DATE   NOT NULL,
    note       TEXT   NULL,
    UNIQUE KEY uq_id_trip_day (trip_id, day_number),
    INDEX idx_id_trip_id (trip_id),
    FOREIGN KEY fk_id_trip (trip_id) REFERENCES trips(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────── PLACES ───────────────
CREATE TABLE places (
    id                BIGINT AUTO_INCREMENT PRIMARY KEY,
    name              VARCHAR(255)  NOT NULL,
    address           VARCHAR(500)  NULL,
    city              VARCHAR(100)  NOT NULL,
    country           VARCHAR(100)  NOT NULL DEFAULT 'Vietnam',
    latitude          DECIMAL(10,8) NULL,
    longitude         DECIMAL(11,8) NULL,
    type              ENUM('ATTRACTION','RESTAURANT','HOTEL','CAFE','SHOPPING','TRANSPORT_HUB','OTHER') NOT NULL,
    rating            DECIMAL(2,1)  NULL,
    phone_number      VARCHAR(20)   NULL,
    website           VARCHAR(500)  NULL,
    opening_hours     JSON          NULL,
    image_url         VARCHAR(500)  NULL,
    price_range       VARCHAR(10)   NULL,
    is_user_generated TINYINT(1)    NOT NULL DEFAULT 0,
    created_by        BIGINT        NULL,
    created_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_places_city (city),
    INDEX idx_places_type (type),
    FULLTEXT INDEX ft_places_name (name),
    FOREIGN KEY fk_places_created_by (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────── ACTIVITIES ───────────────
CREATE TABLE activities (
    id               BIGINT AUTO_INCREMENT PRIMARY KEY,
    itinerary_day_id BIGINT       NOT NULL,
    place_id         BIGINT       NULL,
    name             VARCHAR(255) NOT NULL,
    description      TEXT         NULL,
    start_time       TIME         NULL,
    end_time         TIME         NULL,
    sort_order       INT          NOT NULL DEFAULT 0,
    type             ENUM('SIGHTSEEING','FOOD','ACCOMMODATION','TRANSPORT','SHOPPING','ENTERTAINMENT','OTHER') NOT NULL DEFAULT 'OTHER',
    estimated_cost   DECIMAL(12,2) NULL,
    status           ENUM('PLANNED','DONE','SKIPPED') NOT NULL DEFAULT 'PLANNED',
    note             TEXT         NULL,
    image_url        VARCHAR(500) NULL,
    created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_act_day_id (itinerary_day_id),
    INDEX idx_act_sort (itinerary_day_id, sort_order),
    FOREIGN KEY fk_act_day (itinerary_day_id) REFERENCES itinerary_days(id) ON DELETE CASCADE,
    FOREIGN KEY fk_act_place (place_id) REFERENCES places(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────── SAVED PLACES ───────────────
CREATE TABLE saved_places (
    id       BIGINT AUTO_INCREMENT PRIMARY KEY,
    trip_id  BIGINT   NOT NULL,
    place_id BIGINT   NOT NULL,
    saved_by BIGINT   NOT NULL,
    saved_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_sp_trip_place (trip_id, place_id),
    FOREIGN KEY fk_sp_trip  (trip_id)  REFERENCES trips(id)  ON DELETE CASCADE,
    FOREIGN KEY fk_sp_place (place_id) REFERENCES places(id) ON DELETE CASCADE,
    FOREIGN KEY fk_sp_user  (saved_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────── EXPENSES ───────────────
CREATE TABLE expenses (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    trip_id      BIGINT        NOT NULL,
    name         VARCHAR(255)  NOT NULL,
    amount       DECIMAL(15,2) NOT NULL,
    category     ENUM('FOOD','TRANSPORT','ACCOMMODATION','ENTERTAINMENT','SHOPPING','OTHER') NOT NULL,
    expense_date DATE          NOT NULL,
    paid_by      BIGINT        NOT NULL,
    note         TEXT          NULL,
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_exp_trip_id (trip_id),
    INDEX idx_exp_paid_by (paid_by),
    INDEX idx_exp_category (category),
    FOREIGN KEY fk_exp_trip    (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    FOREIGN KEY fk_exp_paid_by (paid_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────── EXPENSE SPLITS ───────────────
CREATE TABLE expense_splits (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    expense_id BIGINT        NOT NULL,
    user_id    BIGINT        NOT NULL,
    amount     DECIMAL(15,2) NOT NULL,
    is_settled TINYINT(1)    NOT NULL DEFAULT 0,
    settled_at DATETIME      NULL,
    UNIQUE KEY uq_es_expense_user (expense_id, user_id),
    FOREIGN KEY fk_es_expense (expense_id) REFERENCES expenses(id) ON DELETE CASCADE,
    FOREIGN KEY fk_es_user    (user_id)    REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────── CHAT CONVERSATIONS ───────────────
CREATE TABLE chat_conversations (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT       NOT NULL,
    trip_id         BIGINT       NULL,
    title           VARCHAR(255) NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_message_at DATETIME     NULL,
    INDEX idx_cc_user_id (user_id),
    FOREIGN KEY fk_cc_user (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY fk_cc_trip (trip_id) REFERENCES trips(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────── CHAT MESSAGES ───────────────
CREATE TABLE chat_messages (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    conversation_id BIGINT   NOT NULL,
    role            ENUM('USER','ASSISTANT','SYSTEM') NOT NULL,
    content         TEXT     NOT NULL,
    token_count     INT      NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cm_conv_id (conversation_id),
    FOREIGN KEY fk_cm_conv (conversation_id) REFERENCES chat_conversations(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────── AI GENERATION LOGS ───────────────
CREATE TABLE ai_generation_logs (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id        BIGINT       NOT NULL,
    trip_id        BIGINT       NULL,
    feature_type   ENUM('GENERATE_ITINERARY','CHAT','SUGGEST_PLACES','OPTIMIZE_ITINERARY') NOT NULL,
    prompt_summary VARCHAR(500) NULL,
    input_tokens   INT          NULL,
    output_tokens  INT          NULL,
    duration_ms    BIGINT       NULL,
    is_success     TINYINT(1)   NOT NULL DEFAULT 1,
    error_message  TEXT         NULL,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_agl_user_id (user_id),
    INDEX idx_agl_feature (feature_type),
    FOREIGN KEY fk_agl_user (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY fk_agl_trip (trip_id) REFERENCES trips(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────── SEED DATA (Admin) ───────────────
-- Password: Admin@123 (BCrypt hash)
INSERT INTO users (full_name, email, password_hash, role, status, email_verified_at)
VALUES ('System Admin', 'admin@travelmate.ai',
        '$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3oW9sZqK0K',
        'ADMIN', 'ACTIVE', NOW());
