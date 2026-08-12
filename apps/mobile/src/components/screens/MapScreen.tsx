import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { AppScreen, Brand, EmptyState } from '@/components/ui';
import { palette, shadows } from '@/constants/design';
import { useTravel } from '@/context/TravelContext';
import { formatDate } from '@/lib/api';

/**
 * react-native-maps ships native view bindings that cannot be bundled for web.
 * Keep the full interactive map in map.tsx and provide a lightweight web view
 * so designers can review the rest of the product in a browser.
 */
export default function MapWebScreen() {
  const { activeTrip, trips, setActiveTripId } = useTravel();

  if (!activeTrip) {
    return (
      <AppScreen>
        <View style={styles.header}>
          <Brand compact />
          <Text style={styles.heading}>Bản đồ hành trình</Text>
        </View>
        <EmptyState
          icon="navigate-outline"
          title="Chưa chọn chuyến đi"
          message="Tạo hoặc chọn một chuyến đi để mở bản đồ địa điểm có ngữ cảnh."
        />
      </AppScreen>
    );
  }

  const trip = activeTrip;

  function switchTrip() {
    if (trips.length < 2) return;
    const currentIndex = trips.findIndex((candidate) => candidate.id === trip.id);
    setActiveTripId(trips[(currentIndex + 1) % trips.length].id);
  }

  return (
    <AppScreen style={styles.screen}>
      <Brand compact />
      <View style={styles.mapPreview}>
        <View style={styles.grid} />
        <View style={[styles.road, styles.roadOne]} />
        <View style={[styles.road, styles.roadTwo]} />
        <View style={[styles.pin, styles.pinOne]}><Ionicons name="location" size={24} color={palette.forest} /></View>
        <View style={[styles.pin, styles.pinTwo]}><Ionicons name="restaurant" size={17} color={palette.ink} /></View>
        <View style={[styles.pin, styles.pinThree]}><Ionicons name="camera" size={17} color={palette.ink} /></View>

        <View style={styles.tripCard}>
          <Text style={styles.eyebrow}>AI TRAVEL MAP · BẢN WEB</Text>
          <Text style={styles.destination}>{trip.destination}</Text>
          <Text style={styles.meta}>{formatDate(trip.startDate)} — {trip.durationDays} ngày</Text>
          <Pressable disabled={trips.length < 2} onPress={switchTrip} style={styles.switchButton}>
            <Ionicons name={trips.length > 1 ? 'swap-horizontal' : 'map-outline'} size={18} color={palette.white} />
          </Pressable>
        </View>

        <View style={styles.notice}>
          <Ionicons name="phone-portrait-outline" size={20} color={palette.forest} />
          <View style={styles.noticeCopy}>
            <Text style={styles.noticeTitle}>Bản đồ tương tác có trên ứng dụng mobile</Text>
            <Text style={styles.noticeText}>Bản web dùng chế độ xem trước để đội UX/UI kiểm tra toàn bộ luồng giao diện.</Text>
          </View>
        </View>
      </View>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  screen: { gap: 12, paddingBottom: 106 },
  header: { gap: 28 },
  heading: { color: palette.ink, fontSize: 30, fontWeight: '900', letterSpacing: -1.2 },
  mapPreview: { flex: 1, minHeight: 560, overflow: 'hidden', backgroundColor: '#DDE3D8', borderWidth: 5, borderColor: 'rgba(247,247,244,0.9)', borderRadius: 29, ...shadows.dark },
  grid: { ...StyleSheet.absoluteFillObject, opacity: 0.4, backgroundColor: '#D9E2D2' },
  road: { position: 'absolute', height: 28, backgroundColor: '#F7F5EA', borderWidth: 1, borderColor: '#E9E4CF', borderRadius: 20 },
  roadOne: { width: '125%', top: '42%', left: '-12%', transform: [{ rotate: '-18deg' }] },
  roadTwo: { width: '110%', top: '60%', left: '-5%', transform: [{ rotate: '28deg' }] },
  pin: { position: 'absolute', width: 46, height: 46, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderWidth: 4, borderColor: palette.white, borderRadius: 23, ...shadows.card },
  pinOne: { top: '34%', left: '47%' },
  pinTwo: { top: '54%', left: '18%' },
  pinThree: { top: '47%', right: '15%' },
  tripCard: { position: 'absolute', top: 12, left: 12, right: 12, padding: 18, backgroundColor: 'rgba(247,247,244,0.97)', borderRadius: 22, ...shadows.card },
  eyebrow: { color: palette.forest, fontSize: 8, fontWeight: '900', letterSpacing: 1.2 },
  destination: { marginTop: 5, color: palette.ink, fontSize: 26, fontWeight: '900', letterSpacing: -0.9 },
  meta: { marginTop: 3, color: palette.muted, fontSize: 10 },
  switchButton: { position: 'absolute', top: 18, right: 18, width: 42, height: 42, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.ink, borderRadius: 14 },
  notice: { position: 'absolute', left: 12, right: 12, bottom: 12, padding: 16, flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: 'rgba(247,247,244,0.97)', borderRadius: 20, ...shadows.card },
  noticeCopy: { flex: 1 },
  noticeTitle: { color: palette.ink, fontSize: 12, fontWeight: '900' },
  noticeText: { marginTop: 3, color: palette.muted, fontSize: 9, lineHeight: 14 },
});
