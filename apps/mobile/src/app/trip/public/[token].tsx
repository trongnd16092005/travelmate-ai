import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { router, useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ImageBackground, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LoadingState, PrimaryButton } from '@/components/ui';
import { palette, radii, shadows } from '@/constants/design';
import { useSession } from '@/context/SessionContext';
import { useDestinationImage } from '@/hooks/useTravelImage';
import { apiRequest, formatCompactMoney, formatDate, initials, TripDetail } from '@/lib/api';

export default function PublicTripScreen() {
  const { token } = useLocalSearchParams<{ token: string }>();
  const { signedIn } = useSession();
  const [trip, setTrip] = useState<TripDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const tripImage = useDestinationImage(trip?.destination, trip?.coverImageUrl);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError('');
    try {
      setTrip(await apiRequest<TripDetail>(`/api/v1/trips/public/${encodeURIComponent(token)}`));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Liên kết chuyến đi không còn khả dụng.');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load().catch(() => undefined);
  }, [load]);

  function close() {
    if (router.canGoBack()) router.back();
    else router.replace('/');
  }

  if (loading) return <View style={styles.stateScreen}><LoadingState label="Đang mở chuyến đi được chia sẻ..." /></View>;
  if (!trip || error) return <View style={styles.stateScreen}><SafeAreaView style={styles.stateSafe}><View style={styles.errorIcon}><Ionicons name="link-outline" size={30} color={palette.forest} /></View><Text style={styles.errorTitle}>Không mở được chuyến đi</Text><Text style={styles.errorCopy}>{error || 'Liên kết có thể đã bị chủ chuyến tắt.'}</Text><PrimaryButton label="Thử lại" icon="refresh" onPress={() => load().catch(() => undefined)} /><PrimaryButton label="Quay lại" variant="ghost" onPress={close} /></SafeAreaView></View>;

  return (
    <View style={styles.screen}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
        <ImageBackground source={tripImage.source} style={styles.hero} imageStyle={styles.heroImage}>
          <LinearGradient colors={['rgba(8,16,10,0.06)', 'rgba(8,16,10,0.88)']} style={[StyleSheet.absoluteFill, styles.heroImage]} />
          <SafeAreaView style={styles.heroSafe} edges={['top']}>
            <View style={styles.heroTop}>
              <Pressable onPress={close} style={styles.iconButton}><Ionicons name="arrow-back" size={20} color={palette.white} /></Pressable>
              <View style={styles.publicPill}><View style={styles.publicDot} /><Text style={styles.publicPillText}>CHUYẾN ĐI ĐƯỢC CHIA SẺ</Text></View>
            </View>
            <View style={styles.heroCopy}>
              <Text style={styles.destination}>{trip.destination}</Text>
              <Text style={styles.tripName}>{trip.name}</Text>
              <Text style={styles.owner}>Hành trình của {trip.owner.fullName}</Text>
            </View>
          </SafeAreaView>
        </ImageBackground>

        <View style={styles.body}>
          <View style={styles.stats}>
            <Stat icon="calendar-outline" value={`${trip.durationDays} ngày`} label={`${formatDate(trip.startDate)} – ${formatDate(trip.endDate)}`} />
            <View style={styles.statDivider} />
            <Stat icon="people-outline" value={`${trip.numPeople} người`} label={`${trip.members.length} thành viên đã tham gia`} />
            <View style={styles.statDivider} />
            <Stat icon="wallet-outline" value={formatCompactMoney(trip.budget)} label="Ngân sách dự kiến" />
          </View>

          {trip.description ? <View style={styles.card}><Text style={styles.eyebrow}>VỀ HÀNH TRÌNH</Text><Text style={styles.description}>{trip.description}</Text></View> : null}

          <View style={styles.card}>
            <View style={styles.sectionHeader}><View><Text style={styles.eyebrow}>ĐI CÙNG NHAU</Text><Text style={styles.sectionTitle}>{trip.members.length} thành viên</Text></View><Ionicons name="people" size={22} color={palette.forest} /></View>
            <View style={styles.members}>
              {trip.members.map((member) => <View key={member.memberId} style={styles.memberRow}><View style={styles.avatar}><Text style={styles.avatarText}>{initials(member.fullName)}</Text></View><View style={styles.memberCopy}><Text style={styles.memberName}>{member.fullName}</Text><Text style={styles.memberRole}>{member.role === 'OWNER' ? 'Chủ chuyến' : member.role === 'EDITOR' ? 'Cùng lên kế hoạch' : 'Thành viên'}</Text></View></View>)}
            </View>
          </View>

          <View style={styles.privacy}><Ionicons name="shield-checkmark-outline" size={18} color={palette.forest} /><Text style={styles.privacyText}>Đây là bản xem chỉ đọc. Chi phí chi tiết và dữ liệu cá nhân không được hiển thị qua liên kết công khai.</Text></View>
          {!signedIn ? <PrimaryButton label="Đăng nhập TravelMate" icon="log-in-outline" onPress={() => router.push('/(auth)/login')} /> : <PrimaryButton label="Về chuyến đi của tôi" icon="map-outline" onPress={() => router.replace('/(tabs)/trips')} />}
        </View>
      </ScrollView>
    </View>
  );
}

function Stat({ icon, value, label }: { icon: keyof typeof Ionicons.glyphMap; value: string; label: string }) {
  return <View style={styles.stat}><View style={styles.statIcon}><Ionicons name={icon} size={17} color={palette.ink} /></View><Text style={styles.statValue}>{value}</Text><Text style={styles.statLabel} numberOfLines={2}>{label}</Text></View>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.cream },
  content: { paddingBottom: 34 },
  stateScreen: { flex: 1, justifyContent: 'center', backgroundColor: palette.cream },
  stateSafe: { padding: 26, alignItems: 'center', gap: 12 },
  errorIcon: { width: 64, height: 64, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 22 },
  errorTitle: { marginTop: 7, color: palette.ink, fontSize: 25, fontWeight: '900', letterSpacing: -1 },
  errorCopy: { marginBottom: 7, color: palette.muted, fontSize: 11, lineHeight: 17, textAlign: 'center' },
  hero: { height: 400 },
  heroImage: { borderBottomLeftRadius: 32, borderBottomRightRadius: 32 },
  heroSafe: { flex: 1, padding: 18 },
  heroTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  iconButton: { width: 43, height: 43, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(10,20,13,0.50)', borderWidth: 1, borderColor: palette.whiteLine, borderRadius: 15 },
  publicPill: { minHeight: 34, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', gap: 7, backgroundColor: 'rgba(255,255,255,0.88)', borderRadius: radii.pill },
  publicDot: { width: 7, height: 7, backgroundColor: palette.forest, borderRadius: 4 },
  publicPillText: { color: palette.ink, fontSize: 7, fontWeight: '900', letterSpacing: 0.7 },
  heroCopy: { marginTop: 'auto', paddingBottom: 8 },
  destination: { color: palette.lime, fontSize: 8, fontWeight: '900', letterSpacing: 1.4 },
  tripName: { marginTop: 5, color: palette.white, fontSize: 36, lineHeight: 39, fontWeight: '900', letterSpacing: -1.7 },
  owner: { marginTop: 8, color: 'rgba(255,255,255,0.72)', fontSize: 10, fontWeight: '700' },
  body: { padding: 18, gap: 15 },
  stats: { padding: 15, flexDirection: 'row', alignItems: 'stretch', backgroundColor: palette.paper, borderRadius: radii.xl, ...shadows.card },
  stat: { flex: 1, alignItems: 'center' },
  statIcon: { width: 35, height: 35, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 12 },
  statValue: { marginTop: 7, color: palette.ink, fontSize: 10, fontWeight: '900', textAlign: 'center' },
  statLabel: { marginTop: 3, color: palette.muted, fontSize: 6.8, lineHeight: 10, textAlign: 'center' },
  statDivider: { width: 1, marginHorizontal: 5, backgroundColor: palette.line },
  card: { padding: 18, backgroundColor: palette.paper, borderRadius: radii.xl, ...shadows.card },
  eyebrow: { color: palette.forest, fontSize: 7.5, fontWeight: '900', letterSpacing: 1.3 },
  description: { marginTop: 8, color: palette.inkSoft, fontSize: 11, lineHeight: 18 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  sectionTitle: { marginTop: 3, color: palette.ink, fontSize: 18, fontWeight: '900' },
  members: { marginTop: 13, gap: 10 },
  memberRow: { minHeight: 47, flexDirection: 'row', alignItems: 'center', gap: 10 },
  avatar: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 14 },
  avatarText: { color: palette.ink, fontSize: 10, fontWeight: '900' },
  memberCopy: { flex: 1 },
  memberName: { color: palette.ink, fontSize: 10, fontWeight: '900' },
  memberRole: { marginTop: 2, color: palette.muted, fontSize: 8 },
  privacy: { padding: 14, flexDirection: 'row', alignItems: 'flex-start', gap: 9, backgroundColor: palette.sage, borderRadius: radii.md },
  privacyText: { flex: 1, color: palette.inkSoft, fontSize: 8.5, lineHeight: 13 },
});
