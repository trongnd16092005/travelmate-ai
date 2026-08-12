import { Ionicons } from '@expo/vector-icons';
import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Brand, PrimaryButton } from '@/components/ui';
import { palette, radii, shadows } from '@/constants/design';
import { useSession } from '@/context/SessionContext';
import { useTravel } from '@/context/TravelContext';
import { apiRequest, ApiError } from '@/lib/api';

type AcceptanceState = 'waiting' | 'accepting' | 'success' | 'error';

type AcceptanceRequest = {
  token: string;
  promise: Promise<void>;
};

export default function AcceptInvitationScreen() {
  const { token: tokenParam } = useLocalSearchParams<{ token?: string | string[] }>();
  const token = normalizeToken(tokenParam);
  const { booting, signedIn } = useSession();
  const { reloadTrips } = useTravel();
  const requestRef = useRef<AcceptanceRequest | null>(null);
  const [state, setState] = useState<AcceptanceState>('waiting');
  const [message, setMessage] = useState('Đang kiểm tra lời mời của bạn…');

  useEffect(() => {
    if (booting) return;

    if (!token) {
      setState('error');
      setMessage('Liên kết lời mời không hợp lệ hoặc đã bị thiếu thông tin.');
      return;
    }

    if (!signedIn) {
      const next = `/invitations/accept?token=${token}`;
      router.replace({ pathname: '/(auth)/login', params: { next } });
      return;
    }

    if (!requestRef.current || requestRef.current.token !== token) {
      setState('accepting');
      setMessage('Đang thêm chuyến đi vào tài khoản của bạn…');
      requestRef.current = {
        token,
        promise: apiRequest<{ message: string }>(
          `/api/v1/invitations/accept?token=${encodeURIComponent(token)}`,
        ).then(() => reloadTrips()),
      };
    }

    let mounted = true;
    let navigationTimer: ReturnType<typeof setTimeout> | undefined;
    requestRef.current.promise
      .then(() => {
        if (!mounted) return;
        setState('success');
        setMessage('Bạn đã tham gia chuyến đi. Đang mở danh sách chuyến đi…');
        navigationTimer = setTimeout(() => router.replace('/(tabs)/trips'), 1400);
      })
      .catch((cause: unknown) => {
        if (!mounted) return;
        setState('error');
        setMessage(invitationErrorMessage(cause));
      });

    return () => {
      mounted = false;
      if (navigationTimer) clearTimeout(navigationTimer);
    };
  }, [booting, reloadTrips, signedIn, token]);

  const success = state === 'success';
  const error = state === 'error';

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.screen}>
        <Brand compact />
        <View style={styles.card}>
          <View style={[styles.iconWrap, success && styles.successIcon, error && styles.errorIcon]}>
            <Ionicons
              name={success ? 'checkmark' : error ? 'alert-circle-outline' : 'mail-open-outline'}
              size={34}
              color={success ? palette.ink : error ? palette.danger : palette.ink}
            />
          </View>
          <Text style={styles.eyebrow}>LỜI MỜI CHUYẾN ĐI</Text>
          <Text style={styles.title}>
            {success ? 'Đã tham gia!' : error ? 'Chưa thể nhận lời mời' : 'Đang kết nối chuyến đi'}
          </Text>
          <Text style={styles.message}>{message}</Text>
          {error ? (
            <View style={styles.actions}>
              <PrimaryButton
                label="Đăng nhập tài khoản khác"
                icon="log-in-outline"
                onPress={() => router.replace({
                  pathname: '/(auth)/login',
                  params: token ? { next: `/invitations/accept?token=${token}` } : undefined,
                })}
              />
              <PrimaryButton
                label="Về danh sách chuyến đi"
                icon="map-outline"
                variant="ghost"
                onPress={() => router.replace('/(tabs)/trips')}
              />
            </View>
          ) : success ? (
            <View style={styles.actions}>
              <PrimaryButton label="Mở chuyến đi" icon="arrow-forward" onPress={() => router.replace('/(tabs)/trips')} />
            </View>
          ) : (
            <View style={styles.progress}><View style={styles.progressFill} /></View>
          )}
        </View>
      </View>
    </SafeAreaView>
  );
}

function normalizeToken(value?: string | string[]) {
  const token = (Array.isArray(value) ? value[0] : value)?.trim();
  if (!token || !/^[A-Za-z0-9._~-]+$/.test(token)) return null;
  return token;
}

function invitationErrorMessage(cause: unknown) {
  if (!(cause instanceof ApiError)) return 'Không thể xử lý lời mời lúc này. Vui lòng thử lại.';
  if (cause.code === 'INVITATION_EMAIL_MISMATCH') {
    return 'Lời mời được gửi tới email khác. Hãy đăng nhập đúng tài khoản đã nhận email mời.';
  }
  if (cause.code === 'INVITATION_EXPIRED') return 'Lời mời đã hết hạn. Hãy nhờ chủ chuyến đi gửi lời mời mới.';
  if (cause.code === 'INVITATION_USED' || cause.code === 'MEMBER_ALREADY_EXISTS') {
    return 'Lời mời đã được sử dụng hoặc bạn đã là thành viên của chuyến đi này.';
  }
  if (cause.code === 'INVALID_TOKEN') return 'Liên kết lời mời không hợp lệ.';
  return cause.message || 'Không thể xử lý lời mời lúc này. Vui lòng thử lại.';
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: palette.cream },
  screen: { flex: 1, padding: 20, paddingTop: 18 },
  card: {
    marginTop: 'auto',
    marginBottom: 'auto',
    padding: 26,
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,252,0.92)',
    borderWidth: 1,
    borderColor: palette.line,
    borderRadius: radii.xl,
    ...shadows.card,
  },
  iconWrap: { width: 72, height: 72, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.amber, borderRadius: 24 },
  successIcon: { backgroundColor: palette.lime },
  errorIcon: { backgroundColor: '#FFF0EC' },
  eyebrow: { marginTop: 22, color: '#75911D', fontSize: 9, fontWeight: '900', letterSpacing: 1.5 },
  title: { marginTop: 9, color: palette.ink, fontSize: 28, lineHeight: 32, fontWeight: '900', textAlign: 'center', letterSpacing: -1 },
  message: { maxWidth: 290, marginTop: 12, color: palette.muted, fontSize: 12, lineHeight: 19, textAlign: 'center' },
  actions: { alignSelf: 'stretch', marginTop: 24, gap: 10 },
  progress: { width: 150, height: 5, marginTop: 26, overflow: 'hidden', backgroundColor: '#E3E8E2', borderRadius: radii.pill },
  progressFill: { width: '62%', height: '100%', backgroundColor: palette.lime, borderRadius: radii.pill },
});
