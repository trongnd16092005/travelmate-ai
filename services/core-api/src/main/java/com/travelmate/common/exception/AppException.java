package com.travelmate.common.exception;

import lombok.Getter;
import org.springframework.http.HttpStatus;

@Getter
public class AppException extends RuntimeException {
    private final String errorCode;
    private final HttpStatus status;

    public AppException(String errorCode, String message, HttpStatus status) {
        super(message);
        this.errorCode = errorCode;
        this.status = status;
    }

    // Factory methods
    public static AppException notFound(String resource) {
        return new AppException(resource.toUpperCase() + "_NOT_FOUND",
                resource + " không tồn tại", HttpStatus.NOT_FOUND);
    }
    public static AppException forbidden() {
        return new AppException("FORBIDDEN_ACCESS",
                "Bạn không có quyền thực hiện thao tác này", HttpStatus.FORBIDDEN);
    }
    public static AppException conflict(String code, String message) {
        return new AppException(code, message, HttpStatus.CONFLICT);
    }
    public static AppException badRequest(String code, String message) {
        return new AppException(code, message, HttpStatus.BAD_REQUEST);
    }
    public static AppException unauthorized(String code, String message) {
        return new AppException(code, message, HttpStatus.UNAUTHORIZED);
    }
}
