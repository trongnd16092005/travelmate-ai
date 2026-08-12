import { Ionicons } from '@expo/vector-icons';
import * as Linking from 'expo-linking';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { palette, radii, shadows } from '@/constants/design';
import { apiRequest, initials, Trip, TripDetail, TripInvitation } from '@/lib/api';

type PublicLinkResponse = {
  isPublic: boolean;
  publicToken: string;
};

type InviteRole = 'EDITOR' | 'VIEWER';

function buildPublicLink(token: string) {
  const configuredBase = process.env.EXPO_PUBLIC_SHARE_URL?.replace(/\/$/, '');
  return configuredBase
    ? `${configuredBase}/trip/public/${token}`
    : Linking.createURL(`/trip/public/${token}`);
}

function roleLabel(role: string) {
  if (role === 'OWNER') return 'Chủ chuyến';
  if (role === 'EDITOR') return 'Có thể chỉnh sửa';
  return 'Chỉ xem';
}

export function TripShareSheet({ visible, trip, onClose }: { visible: boolean; trip: Trip; onClose: () => void }) {
  const [detail, setDetail] = useState<TripDetail | null>(null);
  const [invitations, setInvitations] = useState<TripInvitation[]>([]);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<InviteRole>('EDITOR');
  const [loading, setLoading] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [inviting, setInviting] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');

  const isOwner = (detail?.myRole ?? trip.myRole) === 'OWNER';
  const members = detail?.members ?? [];
  const publicEnabled = detail?.isPublic ?? false;

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const nextDetail = await apiRequest<TripDetail>(`/api/v1/trips/${trip.id}`);
      setDetail(nextDetail);
      if (nextDetail.myRole === 'OWNER') {
        try {
          setInvitations(await apiRequest<TripInvitation[]>(`/api/v1/trips/${trip.id}/members/invitations`));
        } catch {
          setInvitations([]);
        }
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Chưa thể tải thông tin chia sẻ.');
    } finally {
      setLoading(false);
    }
  }, [trip.id]);

  useEffect(() => {
    if (!visible) return;
    setNotice('');
    setError('');
    load().catch(() => undefined);
  }, [load, visible]);

  const pendingInvitations = useMemo(
    () => invitations.filter((invitation) => invitation.status === 'PENDING'),
    [invitations],
  );

  async function setPublicLink(enable: boolean) {
    if (!isOwner) return null;
    setSharing(true);
    setError('');
    setNotice('');
    try {
      const result = await apiRequest<PublicLinkResponse>(
        `/api/v1/trips/${trip.id}/public-link?enable=${enable}`,
        { method: 'PATCH' },
      );
      setDetail((current) => current ? {
        ...current,
        isPublic: result.isPublic,
        publicToken: result.publicToken || null,
      } : current);
      setNotice(enable ? 'Đã bật liên kết. Bất kỳ ai có link đều có thể xem chuyến đi.' : 'Đã tắt liên kết công khai.');
      return result.publicToken || null;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Chưa thể cập nhật liên kết.');
      return null;
    } finally {
      setSharing(false);
    }
  }

  async function sharePublicLink() {
    setSharing(true);
    setError('');
    setNotice('');
    try {
      let token = detail?.publicToken ?? null;
      if (!publicEnabled) {
        if (!isOwner) {
          setError('Chủ chuyến cần bật liên kết công khai trước.');
          return;
        }
        const result = await apiRequest<PublicLinkResponse>(
          `/api/v1/trips/${trip.id}/public-link?enable=true`,
          { method: 'PATCH' },
        );
        token = result.publicToken || null;
        setDetail((current) => current ? { ...current, isPublic: true, publicToken: token } : current);
      }
      if (!token) throw new Error('Chưa tạo được liên kết chia sẻ.');

      const url = buildPublicLink(token);
      const message = `Cùng xem chuyến “${trip.name}” đến ${trip.destination} trên TravelMate:\n${url}`;
      const result = await Share.share(
        Platform.OS === 'ios'
          ? { title: trip.name, message: `Cùng xem chuyến “${trip.name}” đến ${trip.destination} trên TravelMate.`, url }
          : { title: trip.name, message },
      );
      if (result.action === Share.sharedAction) setNotice('Đã mở bảng chia sẻ của thiết bị.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Chưa thể mở bảng chia sẻ.');
    } finally {
      setSharing(false);
    }
  }

  async function inviteMember() {
    const normalizedEmail = email.trim().toLowerCase();
    if (!/^\S+@\S+\.\S+$/.test(normalizedEmail)) {
      setError('Nhập địa chỉ email hợp lệ để gửi lời mời.');
      return;
    }
    setInviting(true);
    setError('');
    setNotice('');
    try {
      const invitation = await apiRequest<TripInvitation>(`/api/v1/trips/${trip.id}/members/invite`, {
        method: 'POST',
        body: JSON.stringify({ email: normalizedEmail, role }),
      });
      setInvitations((current) => [invitation, ...current.filter((item) => item.id !== invitation.id)]);
      setEmail('');
      setNotice(`Đã gửi lời mời đến ${normalizedEmail}. Lời mời có hiệu lực trong 7 ngày.`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Chưa thể gửi lời mời.');
    } finally {
      setInviting(false);
    }
  }

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <KeyboardAvoidingView style={styles.backdrop} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <Pressable style={StyleSheet.absoluteFill} onPress={onClose} accessibilityLabel="Đóng chia sẻ chuyến đi" />
        <SafeAreaView style={styles.safeArea} edges={['bottom']}>
          <View style={styles.sheet}>
            <View style={styles.handle} />
            <View style={styles.header}>
              <View style={styles.headerCopy}>
                <Text style={styles.eyebrow}>ĐI CÙNG NHAU</Text>
                <Text style={styles.title}>Chia sẻ chuyến đi</Text>
                <Text style={styles.subtitle} numberOfLines={1}>{trip.name} · {trip.destination}</Text>
              </View>
              <Pressable onPress={onClose} style={styles.closeButton} accessibilityRole="button" accessibilityLabel="Đóng">
                <Ionicons name="close" size={20} color={palette.ink} />
              </Pressable>
            </View>

            {loading ? <View style={styles.loading}><ActivityIndicator color={palette.forest} /><Text style={styles.loadingText}>Đang chuẩn bị quyền chia sẻ...</Text></View> : (
              <ScrollView showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled" contentContainerStyle={styles.content}>
                <View style={styles.publicCard}>
                  <View style={styles.publicIcon}><Ionicons name="link" size={20} color={palette.ink} /></View>
                  <View style={styles.publicCopy}>
                    <Text style={styles.sectionTitle}>Liên kết xem chuyến đi</Text>
                    <Text style={styles.sectionCaption}>{publicEnabled ? 'Ai có liên kết đều xem được bản tóm tắt chuyến đi.' : 'Liên kết đang tắt và chưa ai bên ngoài xem được.'}</Text>
                  </View>
                  {isOwner ? (
                    <Pressable
                      onPress={() => setPublicLink(!publicEnabled)}
                      disabled={sharing}
                      style={[styles.switch, publicEnabled && styles.switchActive]}
                      accessibilityRole="switch"
                      accessibilityState={{ checked: publicEnabled, busy: sharing }}
                    >
                      <View style={[styles.switchThumb, publicEnabled && styles.switchThumbActive]} />
                    </Pressable>
                  ) : <Ionicons name={publicEnabled ? 'checkmark-circle' : 'lock-closed'} size={22} color={publicEnabled ? palette.forest : palette.muted} />}
                </View>

                <Pressable onPress={sharePublicLink} disabled={sharing || (!publicEnabled && !isOwner)} style={({ pressed }) => [styles.shareButton, pressed && styles.buttonPressed, (sharing || (!publicEnabled && !isOwner)) && styles.disabled]}>
                  {sharing ? <ActivityIndicator color={palette.ink} /> : <Ionicons name="share-outline" size={18} color={palette.ink} />}
                  <Text style={styles.shareButtonText}>{publicEnabled ? 'Chia sẻ liên kết' : 'Bật link và chia sẻ'}</Text>
                  {!sharing && <Ionicons name="arrow-forward" size={17} color={palette.ink} />}
                </Pressable>

                <View style={styles.divider} />
                <View style={styles.memberHeader}>
                  <View><Text style={styles.sectionEyebrow}>THÀNH VIÊN</Text><Text style={styles.memberTitle}>{members.length} người trong chuyến</Text></View>
                  <View style={styles.avatarStack}>
                    {members.slice(0, 4).map((member, index) => (
                      <View key={member.memberId} style={[styles.avatar, { marginLeft: index === 0 ? 0 : -8, zIndex: 5 - index }]}>
                        <Text style={styles.avatarText}>{initials(member.fullName)}</Text>
                      </View>
                    ))}
                  </View>
                </View>
                <View style={styles.memberList}>
                  {members.map((member) => (
                    <View key={member.memberId} style={styles.memberRow}>
                      <View style={styles.memberAvatar}><Text style={styles.memberAvatarText}>{initials(member.fullName)}</Text></View>
                      <View style={styles.memberCopy}><Text style={styles.memberName} numberOfLines={1}>{member.fullName}</Text><Text style={styles.memberEmail} numberOfLines={1}>{member.email}</Text></View>
                      <Text style={styles.memberRole}>{roleLabel(member.role)}</Text>
                    </View>
                  ))}
                </View>

                {isOwner && <>
                  <View style={styles.divider} />
                  <View>
                    <Text style={styles.sectionEyebrow}>MỜI CỘNG SỰ</Text>
                    <Text style={styles.inviteTitle}>Thêm người qua email</Text>
                    <Text style={styles.sectionCaption}>Người được mời cần đăng nhập đúng email để tham gia chuyến.</Text>
                  </View>
                  <TextInput
                    value={email}
                    onChangeText={setEmail}
                    placeholder="banbe@example.com"
                    placeholderTextColor="#899089"
                    keyboardType="email-address"
                    autoCapitalize="none"
                    autoCorrect={false}
                    returnKeyType="send"
                    onSubmitEditing={() => inviteMember().catch(() => undefined)}
                    style={styles.emailInput}
                  />
                  <View style={styles.rolePicker}>
                    <RoleOption value="EDITOR" selected={role === 'EDITOR'} onPress={() => setRole('EDITOR')} />
                    <RoleOption value="VIEWER" selected={role === 'VIEWER'} onPress={() => setRole('VIEWER')} />
                  </View>
                  <Pressable onPress={inviteMember} disabled={inviting} style={({ pressed }) => [styles.inviteButton, pressed && styles.buttonPressed, inviting && styles.disabled]}>
                    {inviting ? <ActivityIndicator color={palette.white} /> : <Ionicons name="person-add-outline" size={17} color={palette.white} />}
                    <Text style={styles.inviteButtonText}>Gửi lời mời</Text>
                  </Pressable>
                  {pendingInvitations.length > 0 && <View style={styles.pendingBox}>
                    <Text style={styles.pendingTitle}>ĐANG CHỜ PHẢN HỒI · {pendingInvitations.length}</Text>
                    {pendingInvitations.slice(0, 3).map((invitation) => <View key={invitation.id} style={styles.pendingRow}><Ionicons name="time-outline" size={14} color={palette.muted} /><Text style={styles.pendingEmail} numberOfLines={1}>{invitation.inviteeEmail}</Text><Text style={styles.pendingRole}>{roleLabel(invitation.role)}</Text></View>)}
                  </View>}
                </>}

                {notice ? <View style={styles.notice}><Ionicons name="checkmark-circle" size={16} color={palette.forest} /><Text style={styles.noticeText}>{notice}</Text></View> : null}
                {error ? <View style={styles.error}><Ionicons name="alert-circle" size={16} color={palette.danger} /><Text style={styles.errorText}>{error}</Text></View> : null}
              </ScrollView>
            )}
          </View>
        </SafeAreaView>
      </KeyboardAvoidingView>
    </Modal>
  );
}

function RoleOption({ value, selected, onPress }: { value: InviteRole; selected: boolean; onPress: () => void }) {
  const editor = value === 'EDITOR';
  return <Pressable onPress={onPress} style={[styles.roleOption, selected && styles.roleOptionActive]} accessibilityRole="radio" accessibilityState={{ checked: selected }}>
    <View style={[styles.radio, selected && styles.radioActive]}>{selected && <View style={styles.radioDot} />}</View>
    <View><Text style={styles.roleTitle}>{editor ? 'Cùng chỉnh sửa' : 'Chỉ xem'}</Text><Text style={styles.roleCaption}>{editor ? 'Sửa lịch trình và chi phí' : 'Theo dõi nội dung chuyến đi'}</Text></View>
  </Pressable>;
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(9, 18, 13, 0.58)' },
  safeArea: { maxHeight: '93%' },
  sheet: { maxHeight: '100%', paddingTop: 9, backgroundColor: palette.paper, borderTopLeftRadius: 31, borderTopRightRadius: 31, ...shadows.dark },
  handle: { width: 42, height: 4, alignSelf: 'center', marginBottom: 13, backgroundColor: '#BEC4BC', borderRadius: 3 },
  header: { paddingHorizontal: 20, paddingBottom: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderBottomWidth: 1, borderBottomColor: palette.line },
  headerCopy: { flex: 1, paddingRight: 12 },
  eyebrow: { color: palette.forest, fontSize: 8, fontWeight: '900', letterSpacing: 1.5 },
  title: { marginTop: 4, color: palette.ink, fontSize: 26, lineHeight: 30, fontWeight: '900', letterSpacing: -1.1 },
  subtitle: { marginTop: 3, color: palette.muted, fontSize: 10, fontWeight: '600' },
  closeButton: { width: 41, height: 41, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.cream, borderRadius: 14 },
  content: { padding: 20, paddingBottom: 28, gap: 13 },
  loading: { minHeight: 220, alignItems: 'center', justifyContent: 'center', gap: 10 },
  loadingText: { color: palette.muted, fontSize: 10, fontWeight: '700' },
  publicCard: { minHeight: 78, padding: 13, flexDirection: 'row', alignItems: 'center', gap: 11, backgroundColor: palette.cream, borderRadius: radii.lg },
  publicIcon: { width: 43, height: 43, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 14 },
  publicCopy: { flex: 1 },
  sectionTitle: { color: palette.ink, fontSize: 12, fontWeight: '900' },
  sectionCaption: { marginTop: 3, color: palette.muted, fontSize: 8.5, lineHeight: 13 },
  switch: { width: 45, height: 26, padding: 3, justifyContent: 'center', backgroundColor: '#C6CBC5', borderRadius: 15 },
  switchActive: { backgroundColor: palette.forest },
  switchThumb: { width: 20, height: 20, backgroundColor: palette.white, borderRadius: 10 },
  switchThumbActive: { alignSelf: 'flex-end' },
  shareButton: { minHeight: 50, paddingHorizontal: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9, backgroundColor: palette.lime, borderRadius: radii.md },
  shareButtonText: { flex: 1, color: palette.ink, fontSize: 10, fontWeight: '900', textAlign: 'center' },
  buttonPressed: { transform: [{ scale: 0.985 }], opacity: 0.9 },
  disabled: { opacity: 0.5 },
  divider: { height: 1, marginVertical: 2, backgroundColor: palette.line },
  memberHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  sectionEyebrow: { color: palette.forest, fontSize: 7.5, fontWeight: '900', letterSpacing: 1.3 },
  memberTitle: { marginTop: 3, color: palette.ink, fontSize: 15, fontWeight: '900' },
  avatarStack: { flexDirection: 'row' },
  avatar: { width: 30, height: 30, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderWidth: 2, borderColor: palette.paper, borderRadius: 15 },
  avatarText: { color: palette.ink, fontSize: 8, fontWeight: '900' },
  memberList: { overflow: 'hidden', backgroundColor: palette.white, borderWidth: 1, borderColor: palette.line, borderRadius: radii.md },
  memberRow: { minHeight: 55, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', gap: 9, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: palette.line },
  memberAvatar: { width: 33, height: 33, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.sage, borderRadius: 12 },
  memberAvatarText: { color: palette.forest, fontSize: 9, fontWeight: '900' },
  memberCopy: { flex: 1, minWidth: 0 },
  memberName: { color: palette.ink, fontSize: 9.5, fontWeight: '900' },
  memberEmail: { marginTop: 2, color: palette.muted, fontSize: 7.5 },
  memberRole: { color: palette.forest, fontSize: 7.5, fontWeight: '800' },
  inviteTitle: { marginTop: 3, color: palette.ink, fontSize: 17, fontWeight: '900' },
  emailInput: { minHeight: 50, paddingHorizontal: 14, color: palette.ink, backgroundColor: palette.white, borderWidth: 1, borderColor: palette.line, borderRadius: radii.md, fontSize: 11, fontWeight: '700' },
  rolePicker: { flexDirection: 'row', gap: 8 },
  roleOption: { flex: 1, minHeight: 64, padding: 10, flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: palette.cream, borderWidth: 1, borderColor: 'transparent', borderRadius: radii.md },
  roleOptionActive: { backgroundColor: '#F7EFAE', borderColor: 'rgba(91, 105, 23, 0.18)' },
  radio: { width: 17, height: 17, alignItems: 'center', justifyContent: 'center', borderWidth: 1.5, borderColor: palette.muted, borderRadius: 9 },
  radioActive: { borderColor: palette.forest },
  radioDot: { width: 8, height: 8, backgroundColor: palette.forest, borderRadius: 4 },
  roleTitle: { color: palette.ink, fontSize: 8.5, fontWeight: '900' },
  roleCaption: { maxWidth: 105, marginTop: 2, color: palette.muted, fontSize: 7, lineHeight: 10 },
  inviteButton: { minHeight: 50, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, backgroundColor: palette.forest, borderRadius: radii.md },
  inviteButtonText: { color: palette.white, fontSize: 10, fontWeight: '900' },
  pendingBox: { padding: 12, gap: 9, backgroundColor: palette.cream, borderRadius: radii.md },
  pendingTitle: { color: palette.muted, fontSize: 7, fontWeight: '900', letterSpacing: 1 },
  pendingRow: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  pendingEmail: { flex: 1, color: palette.inkSoft, fontSize: 8.5, fontWeight: '700' },
  pendingRole: { color: palette.forest, fontSize: 7.5, fontWeight: '800' },
  notice: { padding: 11, flexDirection: 'row', alignItems: 'flex-start', gap: 8, backgroundColor: '#E5F1E7', borderRadius: radii.sm },
  noticeText: { flex: 1, color: palette.forest, fontSize: 8.5, lineHeight: 13, fontWeight: '700' },
  error: { padding: 11, flexDirection: 'row', alignItems: 'flex-start', gap: 8, backgroundColor: '#FFF0EC', borderRadius: radii.sm },
  errorText: { flex: 1, color: palette.danger, fontSize: 8.5, lineHeight: 13, fontWeight: '700' },
});
