import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { useMemo, useState } from 'react';
import { ImageBackground, KeyboardAvoidingView, Modal, Platform, Pressable, ScrollView, StyleProp, StyleSheet, Text, TextInput, TextStyle, View, ViewStyle } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { AppScreen, Chip, EmptyState, LoadingState, PrimaryButton, ScreenHeader } from '@/components/ui';
import { palette, radii, shadows } from '@/constants/design';
import { useTravel } from '@/context/TravelContext';
import { useDestinationImage } from '@/hooks/useTravelImage';
import { apiRequest, formatCompactMoney, formatDate, Trip } from '@/lib/api';

const travelStyles = [
  ['RELAXATION', 'Nghỉ dưỡng'],
  ['CULTURE', 'Văn hoá'],
  ['ADVENTURE', 'Phiêu lưu'],
  ['FOOD_TOUR', 'Ẩm thực'],
] as const;

function toDate(offset: number) {
  const date = new Date();
  date.setDate(date.getDate() + offset);
  return date.toISOString().slice(0, 10);
}

export default function TripsScreen() {
  const { trips, activeTripId, loadingTrips, reloadTrips, setActiveTripId } = useTravel();
  const [showCreate, setShowCreate] = useState(false);
  const grouped = useMemo(() => ({
    active: trips.filter((trip) => trip.status === 'ONGOING' || trip.status === 'UPCOMING' || trip.status === 'PLANNING'),
    completed: trips.filter((trip) => trip.status === 'COMPLETED'),
  }), [trips]);

  function openTrip(trip: Trip) {
    setActiveTripId(trip.id);
    router.push({ pathname: '/trip/[id]', params: { id: String(trip.id) } });
  }

  return (
    <AppScreen>
      <ScreenHeader eyebrow="BỘ SƯU TẬP HÀNH TRÌNH" title="Chuyến đi của bạn" subtitle="Mỗi chuyến đi có lịch trình, bản đồ và ngân sách riêng." action={<Pressable style={styles.addButton} onPress={() => setShowCreate(true)}><Ionicons name="add" size={23} color={palette.ink} /></Pressable>} />
      <View style={styles.filters}><Chip label={`${trips.length} hành trình`} icon="map" active /><Chip label="Đang lên kế hoạch" icon="calendar-outline" /><Chip label="Đã hoàn thành" icon="checkmark-circle-outline" /></View>

      {loadingTrips ? <LoadingState /> : trips.length === 0 ? <EmptyState icon="map-outline" title="Bản đồ còn trống" message="Thêm điểm đến đầu tiên để TravelMate bắt đầu dựng hành trình." action={<PrimaryButton label="Tạo chuyến đi" onPress={() => setShowCreate(true)} />} /> : <>
        <View style={styles.sectionHeader}><Text style={styles.sectionTitle}>Đang chờ bạn</Text><Text style={styles.sectionCount}>{grouped.active.length.toString().padStart(2, '0')}</Text></View>
        <View style={styles.tripList}>{grouped.active.map((trip) => <TripCard key={trip.id} trip={trip} active={trip.id === activeTripId} onPress={() => openTrip(trip)} />)}</View>
        {grouped.completed.length > 0 && <><View style={styles.sectionHeader}><Text style={styles.sectionTitle}>Kỷ niệm đã đi qua</Text><Text style={styles.sectionCount}>{grouped.completed.length.toString().padStart(2, '0')}</Text></View><View style={styles.tripList}>{grouped.completed.map((trip) => <TripCard key={trip.id} trip={trip} active={trip.id === activeTripId} onPress={() => openTrip(trip)} />)}</View></>}
      </>}
      <CreateTripModal visible={showCreate} onClose={() => setShowCreate(false)} onCreated={async (trip) => { await reloadTrips(); setActiveTripId(trip.id); setShowCreate(false); router.push({ pathname: '/trip/[id]', params: { id: String(trip.id) } }); }} />
    </AppScreen>
  );
}

function TripCard({ trip, active, onPress }: { trip: Trip; active: boolean; onPress: () => void }) {
  const tripImage = useDestinationImage(trip.destination, trip.coverImageUrl);
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.tripCard, pressed && styles.pressed]}>
      <ImageBackground source={tripImage.source} style={styles.tripArt} imageStyle={styles.tripArtImage}>
        <LinearGradient colors={['rgba(4,24,19,0.04)', 'rgba(4,24,19,0.88)']} style={[StyleSheet.absoluteFill, styles.tripArtImage]} />
        <View style={styles.tripTop}><Chip label={active ? 'ĐANG CHỌN' : trip.status} icon="radio-button-on" active={active} /><View style={styles.rolePill}><Ionicons name="people-outline" size={13} color={palette.white} /><Text style={styles.rolePillText}>{trip.memberCount}</Text></View></View>
        <View style={styles.tripArtCopy}><Text style={styles.tripDestination}>{trip.destination}</Text><Text style={styles.tripName}>{trip.name}</Text></View>
      </ImageBackground>
      <View style={styles.tripInfo}>
        <View style={styles.tripMeta}><View style={styles.tripMetaItem}><Ionicons name="calendar-outline" size={16} color="#76931F" /><Text style={styles.tripMetaText}>{trip.durationDays} ngày</Text></View><View style={styles.tripMetaItem}><Ionicons name="wallet-outline" size={16} color="#76931F" /><Text style={styles.tripMetaText}>{formatCompactMoney(trip.budget)}</Text></View><View style={styles.tripMetaItem}><Ionicons name="people-outline" size={16} color="#76931F" /><Text style={styles.tripMetaText}>{trip.numPeople} người</Text></View></View>
        <View style={styles.tripFooter}><Text style={styles.tripFooterText}>{formatDate(trip.startDate)} — {formatDate(trip.endDate)}</Text><Ionicons name="arrow-forward" size={18} color={palette.ink} /></View>
      </View>
    </Pressable>
  );
}

function CreateTripModal({ visible, onClose, onCreated }: { visible: boolean; onClose: () => void; onCreated: (trip: Trip) => Promise<void> }) {
  const [form, setForm] = useState({ name: '', destination: '', startDate: toDate(7), endDate: toDate(11), budget: '8000000', numPeople: '2', travelStyle: 'CULTURE', description: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function submit() {
    setError('');
    if (!form.name.trim() || !form.destination.trim() || !/^\d{4}-\d{2}-\d{2}$/.test(form.startDate) || !/^\d{4}-\d{2}-\d{2}$/.test(form.endDate)) {
      setError('Nhập tên, điểm đến và ngày theo định dạng YYYY-MM-DD.');
      return;
    }
    if (form.endDate < form.startDate || Number(form.budget) < 0 || Number(form.numPeople) < 1) {
      setError('Ngày kết thúc phải sau ngày đi; ngân sách và số người cần hợp lệ.');
      return;
    }
    setLoading(true);
    try {
      const trip = await apiRequest<Trip>('/api/v1/trips', { method: 'POST', body: JSON.stringify({ ...form, budget: Number(form.budget), numPeople: Number(form.numPeople) }) });
      apiRequest('/api/v1/ai/generate-itinerary', { method: 'POST', body: JSON.stringify({ tripId: trip.id, travelStyle: form.travelStyle, interests: [], specialRequests: form.description }) }).catch(() => undefined);
      await onCreated(trip);
      setForm({ name: '', destination: '', startDate: toDate(7), endDate: toDate(11), budget: '8000000', numPeople: '2', travelStyle: 'CULTURE', description: '' });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Chưa thể tạo chuyến đi.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <KeyboardAvoidingView style={styles.modalBackdrop} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <SafeAreaView style={styles.modalSafe} edges={['bottom']}>
          <View style={styles.modalCard}>
            <View style={styles.modalHandle} />
            <View style={styles.modalHeader}><View><Text style={styles.modalEyebrow}>HÀNH TRÌNH MỚI</Text><Text style={styles.modalTitle}>Bạn muốn đi đâu?</Text></View><Pressable onPress={onClose} style={styles.closeButton}><Ionicons name="close" size={20} color={palette.ink} /></Pressable></View>
            <ScrollView showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled" contentContainerStyle={styles.form}>
              <Field label="Tên chuyến đi" value={form.name} onChangeText={(name) => setForm({ ...form, name })} placeholder="Mùa hè miền Trung" />
              <Field label="Điểm đến" value={form.destination} onChangeText={(destination) => setForm({ ...form, destination })} placeholder="Huế, Đà Nẵng..." />
              <View style={styles.twoColumns}><Field label="Khởi hành" value={form.startDate} onChangeText={(startDate) => setForm({ ...form, startDate })} placeholder="YYYY-MM-DD" style={styles.flexField} /><Field label="Kết thúc" value={form.endDate} onChangeText={(endDate) => setForm({ ...form, endDate })} placeholder="YYYY-MM-DD" style={styles.flexField} /></View>
              <View style={styles.twoColumns}><Field label="Ngân sách" value={form.budget} onChangeText={(budget) => setForm({ ...form, budget })} keyboardType="numeric" style={styles.flexField} /><Field label="Số người" value={form.numPeople} onChangeText={(numPeople) => setForm({ ...form, numPeople })} keyboardType="numeric" style={styles.flexField} /></View>
              <View><Text style={styles.fieldLabel}>Phong cách</Text><View style={styles.styleChips}>{travelStyles.map(([value, label]) => <Chip key={value} label={label} active={form.travelStyle === value} onPress={() => setForm({ ...form, travelStyle: value })} />)}</View></View>
              <Field label="Mong muốn đặc biệt" value={form.description} onChangeText={(description) => setForm({ ...form, description })} placeholder="Ẩm thực, chụp ảnh, đi chậm..." multiline inputStyle={styles.textarea} />
              {error ? <Text style={styles.formError}>{error}</Text> : null}
              <PrimaryButton label="Tạo và để AI lên lịch" icon="sparkles" loading={loading} onPress={submit} />
            </ScrollView>
          </View>
        </SafeAreaView>
      </KeyboardAvoidingView>
    </Modal>
  );
}

function Field({ label, style, inputStyle, ...props }: Omit<React.ComponentProps<typeof TextInput>, 'style'> & { label: string; style?: StyleProp<ViewStyle>; inputStyle?: StyleProp<TextStyle> }) {
  return <View style={[styles.fieldGroup, style]}><Text style={styles.fieldLabel}>{label}</Text><TextInput style={[styles.fieldInput, inputStyle]} placeholderTextColor="#91A09A" {...props} /></View>;
}

const styles = StyleSheet.create({
  addButton: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 15, ...shadows.card },
  filters: { marginHorizontal: -18, paddingHorizontal: 18, flexDirection: 'row', gap: 8, overflow: 'hidden' },
  sectionHeader: { marginTop: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  sectionTitle: { color: palette.ink, fontSize: 19, fontWeight: '900' },
  sectionCount: { color: '#7B9425', fontSize: 11, fontWeight: '900' },
  tripList: { gap: 14 },
  tripCard: { overflow: 'hidden', backgroundColor: 'rgba(255,255,252,0.84)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.94)', borderRadius: radii.xl, ...shadows.card },
  pressed: { transform: [{ scale: 0.99 }], opacity: 0.95 },
  tripArt: { height: 215, overflow: 'hidden' },
  tripArtImage: { borderTopLeftRadius: radii.xl, borderTopRightRadius: radii.xl },
  tripTop: { padding: 14, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  rolePill: { paddingHorizontal: 10, paddingVertical: 7, flexDirection: 'row', alignItems: 'center', gap: 5, backgroundColor: 'rgba(5,29,23,0.55)', borderRadius: radii.pill },
  rolePillText: { color: palette.white, fontSize: 8, fontWeight: '800' },
  tripArtCopy: { marginTop: 'auto', padding: 17 },
  tripDestination: { color: palette.lime, fontSize: 7, fontWeight: '900', letterSpacing: 1.1 },
  tripName: { marginTop: 4, color: palette.white, fontSize: 25, fontWeight: '900', letterSpacing: -1 },
  tripInfo: { padding: 16 },
  tripMeta: { flexDirection: 'row', justifyContent: 'space-between' },
  tripMetaItem: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  tripMetaText: { color: palette.muted, fontSize: 8, fontWeight: '700' },
  tripFooter: { marginTop: 15, paddingTop: 13, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderTopWidth: 1, borderTopColor: palette.line },
  tripFooterText: { color: palette.muted, fontSize: 8 },
  modalBackdrop: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(4,25,20,0.58)' },
  modalSafe: { maxHeight: '93%' },
  modalCard: { maxHeight: '100%', padding: 19, paddingTop: 10, backgroundColor: palette.cream, borderTopLeftRadius: 30, borderTopRightRadius: 30 },
  modalHandle: { width: 42, height: 4, alignSelf: 'center', marginBottom: 18, backgroundColor: '#CBD5CC', borderRadius: 2 },
  modalHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  modalEyebrow: { color: '#76931F', fontSize: 7, fontWeight: '900', letterSpacing: 1.2 },
  modalTitle: { marginTop: 5, color: palette.ink, fontSize: 27, fontWeight: '900', letterSpacing: -1.2 },
  closeButton: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.white, borderRadius: 14 },
  form: { paddingTop: 20, paddingBottom: 24, gap: 14 },
  twoColumns: { flexDirection: 'row', gap: 10 },
  flexField: { flex: 1 },
  fieldGroup: { gap: 7 },
  fieldLabel: { color: palette.inkSoft, fontSize: 8, fontWeight: '900' },
  fieldInput: { minHeight: 50, paddingHorizontal: 14, color: palette.ink, backgroundColor: palette.white, borderWidth: 1, borderColor: palette.line, borderRadius: radii.md, fontSize: 11, fontWeight: '700' },
  textarea: { minHeight: 82, paddingTop: 14, textAlignVertical: 'top' },
  styleChips: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 },
  formError: { padding: 11, color: palette.danger, backgroundColor: '#FFF0EC', borderRadius: radii.sm, fontSize: 9, lineHeight: 15 },
});
