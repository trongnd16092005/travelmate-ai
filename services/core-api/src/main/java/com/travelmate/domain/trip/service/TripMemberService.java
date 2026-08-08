package com.travelmate.domain.trip.service;

import com.travelmate.common.enums.InvitationStatus;
import com.travelmate.common.enums.TripRole;
import com.travelmate.common.exception.AppException;
import com.travelmate.domain.auth.service.EmailService;
import com.travelmate.domain.trip.dto.*;
import com.travelmate.domain.trip.entity.Invitation;
import com.travelmate.domain.trip.entity.Trip;
import com.travelmate.domain.trip.entity.TripMember;
import com.travelmate.domain.trip.repository.InvitationRepository;
import com.travelmate.domain.trip.repository.TripMemberRepository;
import com.travelmate.domain.user.entity.User;
import com.travelmate.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Transactional
public class TripMemberService {

    private final TripMemberRepository tripMemberRepository;
    private final InvitationRepository invitationRepository;
    private final UserRepository userRepository;
    private final TripService tripService;
    private final EmailService emailService;

    // ─── LIST MEMBERS ──────────────────────────────────────
    @Transactional(readOnly = true)
    public List<MemberResponse> getMembers(Long tripId, User user) {
        tripService.getTripAsMember(tripId, user.getId()); // access check
        return tripMemberRepository.findAllByTripId(tripId)
                .stream().map(MemberResponse::from).toList();
    }

    // ─── INVITE ────────────────────────────────────────────
    public InvitationResponse inviteMember(Long tripId, User owner, InviteMemberRequest request) {
        Trip trip = tripService.getTripAsOwner(tripId, owner.getId());

        // Validate role – can't invite as OWNER
        if (request.role() == TripRole.OWNER) {
            throw AppException.badRequest("INVALID_ROLE", "Không thể mời người khác làm OWNER");
        }

        String email = request.email().toLowerCase();

        // Check if already a member
        userRepository.findByEmailAndDeletedAtIsNull(email).ifPresent(u -> {
            if (tripMemberRepository.existsByTripIdAndUserId(tripId, u.getId())) {
                throw AppException.conflict("MEMBER_ALREADY_EXISTS", "Người dùng đã là thành viên của chuyến đi");
            }
        });

        // Check pending invitation
        if (invitationRepository.existsByTripIdAndInviteeEmailAndStatus(
                tripId, email, InvitationStatus.PENDING)) {
            throw AppException.conflict("INVITATION_PENDING", "Đã có lời mời đang chờ cho email này");
        }

        User invitee = userRepository.findByEmailAndDeletedAtIsNull(email).orElse(null);
        String token = UUID.randomUUID().toString();

        Invitation invitation = Invitation.builder()
                .trip(trip)
                .inviter(owner)
                .inviteeEmail(email)
                .invitee(invitee)
                .role(request.role())
                .token(token)
                .expiresAt(LocalDateTime.now().plusDays(7))
                .build();
        invitationRepository.save(invitation);

        // Send email async
        sendInvitationEmailAsync(email, owner.getFullName(), trip.getName(), token, request.role().name());

        return InvitationResponse.from(invitation);
    }

    @Async
    protected void sendInvitationEmailAsync(String email, String inviterName,
                                             String tripName, String token, String role) {
        emailService.sendTripInvitationEmail(email, inviterName, tripName, token, role);
    }

    // ─── ACCEPT INVITATION ─────────────────────────────────
    public void acceptInvitation(String token, User user) {
        Invitation inv = invitationRepository.findByToken(token)
                .orElseThrow(() -> AppException.badRequest("INVALID_TOKEN", "Lời mời không hợp lệ"));

        if (!inv.isPending()) {
            throw AppException.badRequest("INVITATION_USED", "Lời mời này đã được xử lý");
        }
        if (inv.isExpired()) {
            inv.setStatus(InvitationStatus.EXPIRED);
            invitationRepository.save(inv);
            throw AppException.badRequest("INVITATION_EXPIRED", "Lời mời đã hết hạn");
        }

        Long tripId = inv.getTrip().getId();
        if (tripMemberRepository.existsByTripIdAndUserId(tripId, user.getId())) {
            throw AppException.conflict("MEMBER_ALREADY_EXISTS", "Bạn đã là thành viên của chuyến đi này");
        }

        TripMember newMember = TripMember.builder()
                .trip(inv.getTrip())
                .user(user)
                .role(inv.getRole())
                .build();
        tripMemberRepository.save(newMember);

        inv.setStatus(InvitationStatus.ACCEPTED);
        inv.setInvitee(user);
        invitationRepository.save(inv);
    }

    // ─── UPDATE ROLE ───────────────────────────────────────
    public MemberResponse updateMemberRole(Long tripId, Long memberId, User owner,
                                            UpdateMemberRoleRequest request) {
        tripService.getTripAsOwner(tripId, owner.getId()); // verify owner

        TripMember member = tripMemberRepository.findById(memberId)
                .orElseThrow(() -> AppException.notFound("TripMember"));

        if (!member.getTrip().getId().equals(tripId)) throw AppException.notFound("TripMember");
        if (member.isOwner()) throw AppException.badRequest("CANNOT_CHANGE_OWNER", "Không thể thay đổi quyền của Owner");
        if (request.role() == TripRole.OWNER) throw AppException.badRequest("INVALID_ROLE", "Không thể đặt vai trò OWNER qua API này");

        member.setRole(request.role());
        tripMemberRepository.save(member);
        return MemberResponse.from(member);
    }

    // ─── REMOVE MEMBER ─────────────────────────────────────
    public void removeMember(Long tripId, Long memberId, User owner) {
        tripService.getTripAsOwner(tripId, owner.getId());

        TripMember member = tripMemberRepository.findById(memberId)
                .orElseThrow(() -> AppException.notFound("TripMember"));

        if (!member.getTrip().getId().equals(tripId)) throw AppException.notFound("TripMember");
        if (member.isOwner()) throw AppException.badRequest("CANNOT_REMOVE_OWNER", "Không thể xóa Owner");

        tripMemberRepository.delete(member);
    }

    // ─── LEAVE TRIP ────────────────────────────────────────
    public void leaveTrip(Long tripId, User user) {
        TripMember member = tripMemberRepository.findByTripIdAndUserId(tripId, user.getId())
                .orElseThrow(() -> AppException.notFound("TripMember"));

        if (member.isOwner()) {
            throw AppException.badRequest("OWNER_CANNOT_LEAVE",
                    "Owner không thể rời trip. Hãy chuyển quyền Owner trước.");
        }
        tripMemberRepository.delete(member);
    }

    // ─── PENDING INVITATIONS ───────────────────────────────
    @Transactional(readOnly = true)
    public List<InvitationResponse> getPendingInvitations(Long tripId, User owner) {
        tripService.getTripAsOwner(tripId, owner.getId());
        return invitationRepository.findAllByTripIdAndStatus(tripId, InvitationStatus.PENDING)
                .stream().map(InvitationResponse::from).toList();
    }
}
