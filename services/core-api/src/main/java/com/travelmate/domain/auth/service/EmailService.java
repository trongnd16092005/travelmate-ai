package com.travelmate.domain.auth.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class EmailService {

    private final JavaMailSender mailSender;

    @Value("${app.frontend-url}")
    private String frontendUrl;

    @Value("${spring.mail.username}")
    private String fromEmail;

    @Async
    public void sendVerificationEmail(String toEmail, String fullName, String token) {
        try {
            String verifyLink = frontendUrl + "/verify-email?token=" + token;
            SimpleMailMessage message = new SimpleMailMessage();
            message.setFrom(fromEmail);
            message.setTo(toEmail);
            message.setSubject("[TravelMate AI] Xác minh địa chỉ email của bạn");
            message.setText(String.format("""
                    Xin chào %s!
                    
                    Cảm ơn bạn đã đăng ký TravelMate AI.
                    Vui lòng nhấp vào link bên dưới để xác minh email của bạn:
                    
                    %s
                    
                    Link này có hiệu lực trong 24 giờ.
                    
                    Nếu bạn không đăng ký tài khoản này, vui lòng bỏ qua email này.
                    
                    Trân trọng,
                    Đội ngũ TravelMate AI
                    """, fullName, verifyLink));
            mailSender.send(message);
            log.info("Sent verification email to: {}", toEmail);
        } catch (Exception e) {
            log.error("Failed to send verification email to {}: {}", toEmail, e.getMessage());
        }
    }

    @Async
    public void sendPasswordResetEmail(String toEmail, String fullName, String otp) {
        try {
            SimpleMailMessage message = new SimpleMailMessage();
            message.setFrom(fromEmail);
            message.setTo(toEmail);
            message.setSubject("[TravelMate AI] Mã OTP đặt lại mật khẩu");
            message.setText(String.format("""
                    Xin chào %s!
                    
                    Bạn vừa yêu cầu đặt lại mật khẩu cho tài khoản TravelMate AI.
                    
                    Mã OTP của bạn là: %s
                    
                    Mã này có hiệu lực trong 10 phút.
                    
                    Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.
                    
                    Trân trọng,
                    Đội ngũ TravelMate AI
                    """, fullName, otp));
            mailSender.send(message);
            log.info("Sent OTP email to: {}", toEmail);
        } catch (Exception e) {
            log.error("Failed to send OTP email to {}: {}", toEmail, e.getMessage());
        }
    }

    @Async
    public void sendTripInvitationEmail(String toEmail, String inviterName,
                                         String tripName, String inviteToken, String role) {
        try {
            String acceptLink = frontendUrl + "/invitations/accept?token=" + inviteToken;
            SimpleMailMessage message = new SimpleMailMessage();
            message.setFrom(fromEmail);
            message.setTo(toEmail);
            message.setSubject(String.format("[TravelMate AI] %s mời bạn tham gia chuyến đi '%s'",
                    inviterName, tripName));
            message.setText(String.format("""
                    Xin chào!
                    
                    %s đã mời bạn tham gia chuyến đi "%s" trên TravelMate AI với vai trò %s.
                    
                    Nhấp vào link bên dưới để chấp nhận lời mời:
                    %s
                    
                    Lời mời này có hiệu lực trong 7 ngày.
                    
                    Trân trọng,
                    Đội ngũ TravelMate AI
                    """, inviterName, tripName, role, acceptLink));
            mailSender.send(message);
        } catch (Exception e) {
            log.error("Failed to send invitation email to {}: {}", toEmail, e.getMessage());
        }
    }
}
