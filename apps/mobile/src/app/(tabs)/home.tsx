import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { Animated, ImageBackground, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { AppScreen, Avatar, Brand, Chip, EmptyState, GlassCard, LoadingState, PrimaryButton } from '@/components/ui';
import { palette, radii, shadows, tripImages } from '@/constants/design';
import { useSession } from '@/context/SessionContext';
import { useTravel } from '@/context/TravelContext';
import { useDestinationImage } from '@/hooks/useTravelImage';
import { formatCompactMoney, formatDate, Trip } from '@/lib/api';

export default function HomeScreen() {
  const { user } = useSession();
  const { trips, activeTrip, loadingTrips, reloadTrips, setActiveTripId } = useTravel();
  const [entrance] = useState(() => new Animated.Value(0));
  const [contentEntrance] = useState(() => new Animated.Value(0));

  useEffect(() => {
    Animated.stagger(90, [
      Animated.spring(entrance, { toValue: 1, useNativeDriver: true, damping: 17, stiffness: 105 }),
      Animated.spring(contentEntrance, { toValue: 1, useNativeDriver: true, damping: 18, stiffness: 115 }),
    ]).start();
  }, [contentEntrance, entrance]);

  const ongoing = trips.filter((trip) => trip.status === 'ONGOING').length;
  const planned = trips.filter((trip) => trip.status === 'PLANNING' || trip.status === 'UPCOMING').length;

  return (
    <AppScreen>
      <View style={styles.topbar}>
        <Brand compact />
        <View style={styles.topActions}>
          <Pressable style={styles.notification}><Ionicons name="notifications-outline" size={19} color={palette.ink} /><View style={styles.notificationDot} /></Pressable>
          <Avatar name={user?.fullName} size={39} />
        </View>
      </View>

      <Animated.View style={{ opacity: entrance, transform: [{ translateY: entrance.interpolate({ inputRange: [0, 1], outputRange: [18, 0] }) }] }}>
        <Text style={styles.greeting}>Xin chào, {user?.fullName?.split(' ').slice(-1)[0] ?? 'bạn'} 👋</Text>
        <Text style={styles.headline}>Hành trình tiếp theo{`\n`}đang chờ bạn.</Text>
      </Animated.View>

      <Animated.View style={{ opacity: contentEntrance, transform: [{ translateY: contentEntrance.interpolate({ inputRange: [0, 1], outputRange: [24, 0] }) }, { scale: contentEntrance.interpolate({ inputRange: [0, 1], outputRange: [0.975, 1] }) }] }}>
        {loadingTrips ? <LoadingState label="Đang mở bản đồ hành trình..." /> : activeTrip ? (
          <ActiveTripCard trip={activeTrip} onOpen={() => router.push({ pathname: '/trip/[id]', params: { id: String(activeTrip.id) } })} />
        ) : (
          <EmptyState
            icon="airplane-outline"
            title="Chưa có chuyến đi nào"
            message="Tạo chuyến đi đầu tiên, TravelMate AI sẽ giúp bạn lập lịch trình và theo dõi ngân sách."
            action={<PrimaryButton label="Tạo chuyến đi" onPress={() => router.push('/(tabs)/trips')} />}
          />
        )}
      </Animated.View>

      <View style={styles.statsRow}>
        <GlassCard style={styles.statCard}><View style={[styles.statIcon, { backgroundColor: '#E9F9C2' }]}><Ionicons name="map" size={18} color="#6E8E18" /></View><Text style={styles.statValue}>{trips.length}</Text><Text style={styles.statLabel}>Tổng chuyến đi</Text></GlassCard>
        <GlassCard style={styles.statCard}><View style={[styles.statIcon, { backgroundColor: '#DDF2E5' }]}><Ionicons name="navigate" size={18} color="#3C8968" /></View><Text style={styles.statValue}>{ongoing}</Text><Text style={styles.statLabel}>Đang diễn ra</Text></GlassCard>
        <GlassCard style={styles.statCard}><View style={[styles.statIcon, { backgroundColor: '#FFF1D8' }]}><Ionicons name="calendar" size={18} color="#B47A23" /></View><Text style={styles.statValue}>{planned}</Text><Text style={styles.statLabel}>Sắp khởi hành</Text></GlassCard>
      </View>

      <GlassCard dark style={styles.aiCard}>
        <LinearGradient colors={['rgba(210,255,105,0.20)', 'rgba(210,255,105,0.02)']} style={StyleSheet.absoluteFill} />
        <View style={styles.aiIcon}><Ionicons name="sparkles" size={21} color={palette.ink} /></View>
        <View style={styles.aiCopy}><Text style={styles.aiEyebrow}>TRAVELMATE AI</Text><Text style={styles.aiTitle}>Bạn muốn tối ưu điều gì?</Text><Text style={styles.aiText}>Hỏi về lịch trình, địa điểm hoặc ngân sách của chuyến đi hiện tại.</Text></View>
        <Pressable onPress={() => router.push('/(tabs)/ai')} style={styles.aiArrow}><Ionicons name="arrow-forward" size={18} color={palette.ink} /></Pressable>
      </GlassCard>

      {trips.length > 1 && <>
        <View style={styles.sectionHeader}><View><Text style={styles.sectionEyebrow}>BỘ SƯU TẬP CỦA BẠN</Text><Text style={styles.sectionTitle}>Những chuyến đi khác</Text></View><Pressable onPress={reloadTrips}><Ionicons name="refresh" size={19} color={palette.muted} /></Pressable></View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tripRail}>
          {trips.filter((trip) => trip.id !== activeTrip?.id).map((trip) => <MiniTripCard key={trip.id} trip={trip} onPress={() => { setActiveTripId(trip.id); router.push({ pathname: '/trip/[id]', params: { id: String(trip.id) } }); }} />)}
        </ScrollView>
      </>}

      <View style={styles.sectionHeader}><View><Text style={styles.sectionEyebrow}>CẢM HỨNG GẦN ĐÂY</Text><Text style={styles.sectionTitle}>Đi đâu tiếp nhỉ?</Text></View><Chip label="Xem bản đồ" icon="navigate" onPress={() => router.push('/(tabs)/map')} /></View>
      <View style={styles.inspirationGrid}>
        <InspirationCard image={tripImages.coast} place="Phú Yên" caption="Rực rỡ biển xanh" />
        <InspirationCard image={tripImages.mountain} place="Hà Giang" caption="Chạm vào mây" />
      </View>
    </AppScreen>
  );
}

function ActiveTripCard({ trip, onOpen }: { trip: Trip; onOpen: () => void }) {
  const tripImage = useDestinationImage(trip.destination, trip.coverImageUrl);
  return (
    <Pressable onPress={onOpen} style={({ pressed }) => [styles.heroWrap, pressed && { transform: [{ scale: 0.99 }] }]}>
      <ImageBackground source={tripImage.source} style={styles.hero} imageStyle={styles.heroImage}>
        <LinearGradient colors={['rgba(5,28,23,0.12)', 'rgba(5,28,23,0.88)']} style={StyleSheet.absoluteFill} />
        <View style={styles.heroTop}><Chip label={trip.status === 'ONGOING' ? 'ĐANG TRÊN ĐƯỜNG' : 'ĐANG LÊN KẾ HOẠCH'} icon="radio-button-on" active /><View style={styles.heroPeople}><Ionicons name="people" size={14} color={palette.white} /><Text style={styles.heroPeopleText}>{trip.memberCount}</Text></View></View>
        <View style={styles.heroBottom}>
          <Text style={styles.heroPlace}>{trip.destination}</Text>
          <Text style={styles.heroName}>{trip.name}</Text>
          <View style={styles.heroMeta}><Text style={styles.heroMetaText}><Ionicons name="calendar-outline" size={13} /> {trip.durationDays} ngày</Text><View style={styles.heroMetaDivider} /><Text style={styles.heroMetaText}><Ionicons name="wallet-outline" size={13} /> {formatCompactMoney(trip.budget)}</Text></View>
          <View style={styles.heroFooter}><Text style={styles.heroFooterText}>{formatDate(trip.startDate)}</Text><View style={styles.openPill}><Text style={styles.openPillText}>Mở hành trình</Text><Ionicons name="arrow-forward" size={14} color={palette.ink} /></View></View>
        </View>
      </ImageBackground>
    </Pressable>
  );
}

function MiniTripCard({ trip, onPress }: { trip: Trip; onPress: () => void }) {
  const tripImage = useDestinationImage(trip.destination, trip.coverImageUrl);
  return <Pressable onPress={onPress} style={styles.miniTrip}><ImageBackground source={tripImage.source} style={styles.miniTripImage} imageStyle={{ borderRadius: radii.lg }}><LinearGradient colors={['transparent', 'rgba(5,28,23,0.86)']} style={[StyleSheet.absoluteFill, { borderRadius: radii.lg }]} /><View style={styles.miniTripCopy}><Text style={styles.miniTripDestination}>{trip.destination}</Text><Text style={styles.miniTripName} numberOfLines={1}>{trip.name}</Text><Text style={styles.miniTripMeta}>{trip.durationDays} ngày • {formatCompactMoney(trip.budget)}</Text></View></ImageBackground></Pressable>;
}

function InspirationCard({ image, place, caption }: { image: number; place: string; caption: string }) {
  return <ImageBackground source={image} style={styles.inspiration} imageStyle={styles.inspirationImage}><LinearGradient colors={['transparent', 'rgba(5,28,23,0.83)']} style={[StyleSheet.absoluteFill, styles.inspirationImage]} /><View style={styles.inspirationCopy}><Text style={styles.inspirationCaption}>{caption.toUpperCase()}</Text><Text style={styles.inspirationPlace}>{place}</Text></View></ImageBackground>;
}

const styles = StyleSheet.create({
  topbar: { minHeight: 50, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  topActions: { flexDirection: 'row', alignItems: 'center', gap: 9 },
  notification: { width: 39, height: 39, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.68)', borderRadius: 14 },
  notificationDot: { width: 6, height: 6, position: 'absolute', top: 8, right: 8, backgroundColor: palette.coral, borderRadius: 3 },
  greeting: { marginTop: 14, color: palette.muted, fontSize: 11, fontWeight: '700' },
  headline: { marginTop: 5, color: palette.ink, fontSize: 32, lineHeight: 35, fontWeight: '900', letterSpacing: -1.6 },
  heroWrap: { borderRadius: radii.xl, ...shadows.dark },
  hero: { height: 360, overflow: 'hidden', borderRadius: radii.xl },
  heroImage: { borderRadius: radii.xl },
  heroTop: { padding: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  heroPeople: { paddingHorizontal: 11, paddingVertical: 8, flexDirection: 'row', alignItems: 'center', gap: 5, backgroundColor: 'rgba(7,38,30,0.54)', borderWidth: 1, borderColor: palette.whiteLine, borderRadius: radii.pill },
  heroPeopleText: { color: palette.white, fontSize: 9, fontWeight: '800' },
  heroBottom: { marginTop: 'auto', padding: 20 },
  heroPlace: { color: palette.lime, fontSize: 8, fontWeight: '900', letterSpacing: 1.3 },
  heroName: { marginTop: 6, color: palette.white, fontSize: 31, lineHeight: 34, fontWeight: '900', letterSpacing: -1.3 },
  heroMeta: { marginTop: 10, flexDirection: 'row', alignItems: 'center', gap: 12 },
  heroMetaText: { color: 'rgba(255,255,255,0.72)', fontSize: 10 },
  heroMetaDivider: { width: 1, height: 11, backgroundColor: 'rgba(255,255,255,0.25)' },
  heroFooter: { marginTop: 18, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  heroFooterText: { color: 'rgba(255,255,255,0.55)', fontSize: 8, fontWeight: '700' },
  openPill: { paddingHorizontal: 13, paddingVertical: 10, flexDirection: 'row', alignItems: 'center', gap: 7, backgroundColor: palette.lime, borderRadius: radii.pill },
  openPillText: { color: palette.ink, fontSize: 8, fontWeight: '900' },
  statsRow: { flexDirection: 'row', gap: 9 },
  statCard: { flex: 1, minWidth: 0, padding: 12, borderRadius: 20 },
  statIcon: { width: 34, height: 34, marginBottom: 12, alignItems: 'center', justifyContent: 'center', borderRadius: 12 },
  statValue: { color: palette.ink, fontSize: 22, fontWeight: '900' },
  statLabel: { marginTop: 3, color: palette.muted, fontSize: 7, lineHeight: 11, fontWeight: '700' },
  aiCard: { minHeight: 122, padding: 16, flexDirection: 'row', alignItems: 'center', gap: 12, overflow: 'hidden' },
  aiIcon: { width: 46, height: 46, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 16 },
  aiCopy: { flex: 1 },
  aiEyebrow: { color: palette.lime, fontSize: 6, fontWeight: '900', letterSpacing: 1.1 },
  aiTitle: { marginTop: 4, color: palette.white, fontSize: 14, fontWeight: '900' },
  aiText: { marginTop: 4, color: 'rgba(255,255,255,0.52)', fontSize: 8, lineHeight: 13 },
  aiArrow: { width: 36, height: 36, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 13 },
  sectionHeader: { marginTop: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  sectionEyebrow: { color: '#78921F', fontSize: 7, fontWeight: '900', letterSpacing: 1.1 },
  sectionTitle: { marginTop: 5, color: palette.ink, fontSize: 20, fontWeight: '900', letterSpacing: -0.8 },
  tripRail: { gap: 12, paddingRight: 18 },
  miniTrip: { width: 250, ...shadows.card },
  miniTripImage: { height: 172, justifyContent: 'flex-end' },
  miniTripCopy: { padding: 16 },
  miniTripDestination: { color: palette.lime, fontSize: 7, fontWeight: '900', letterSpacing: 1 },
  miniTripName: { marginTop: 4, color: palette.white, fontSize: 17, fontWeight: '900' },
  miniTripMeta: { marginTop: 5, color: 'rgba(255,255,255,0.58)', fontSize: 8 },
  inspirationGrid: { height: 230, flexDirection: 'row', gap: 10 },
  inspiration: { flex: 1, justifyContent: 'flex-end', overflow: 'hidden', borderRadius: radii.lg },
  inspirationImage: { borderRadius: radii.lg },
  inspirationCopy: { padding: 15 },
  inspirationCaption: { color: palette.lime, fontSize: 6, fontWeight: '900', letterSpacing: 0.9 },
  inspirationPlace: { marginTop: 4, color: palette.white, fontSize: 19, fontWeight: '900' },
});
