import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useEffect, useRef, useState } from 'react';
import { Animated, Image, Linking, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import MapView, { Marker, PROVIDER_DEFAULT, Region } from 'react-native-maps';
import { AppScreen, Brand, EmptyState, LoadingState } from '@/components/ui';
import { palette, radii, shadows } from '@/constants/design';
import { useTravel } from '@/context/TravelContext';
import { usePlaceImage } from '@/hooks/useTravelImage';
import { apiRequest, formatDate, parseJsonData, PlaceSuggestion, PlaceSuggestionResponse } from '@/lib/api';

const fallbackRegions: Record<string, Region> = {
  'hà nội': { latitude: 21.0278, longitude: 105.8342, latitudeDelta: 0.18, longitudeDelta: 0.18 },
  hanoi: { latitude: 21.0278, longitude: 105.8342, latitudeDelta: 0.18, longitudeDelta: 0.18 },
  'hồ chí minh': { latitude: 10.7769, longitude: 106.7009, latitudeDelta: 0.2, longitudeDelta: 0.2 },
  'sài gòn': { latitude: 10.7769, longitude: 106.7009, latitudeDelta: 0.2, longitudeDelta: 0.2 },
  huế: { latitude: 16.4637, longitude: 107.5909, latitudeDelta: 0.14, longitudeDelta: 0.14 },
  'thừa thiên huế': { latitude: 16.4637, longitude: 107.5909, latitudeDelta: 0.14, longitudeDelta: 0.14 },
  'đà nẵng': { latitude: 16.0544, longitude: 108.2022, latitudeDelta: 0.16, longitudeDelta: 0.16 },
  'hội an': { latitude: 15.8801, longitude: 108.338, latitudeDelta: 0.12, longitudeDelta: 0.12 },
  'hà giang': { latitude: 22.8026, longitude: 104.9784, latitudeDelta: 0.45, longitudeDelta: 0.45 },
  'phú yên': { latitude: 13.0882, longitude: 109.0929, latitudeDelta: 0.4, longitudeDelta: 0.4 },
  'đà lạt': { latitude: 11.9404, longitude: 108.4583, latitudeDelta: 0.2, longitudeDelta: 0.2 },
  'ninh bình': { latitude: 20.2506, longitude: 105.9745, latitudeDelta: 0.3, longitudeDelta: 0.3 },
  sapa: { latitude: 22.3364, longitude: 103.8438, latitudeDelta: 0.24, longitudeDelta: 0.24 },
};

const lightMapStyle = [
  { elementType: 'geometry', stylers: [{ color: '#e7e8e3' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#535a53' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#f4f4f0' }] },
  { featureType: 'poi', elementType: 'geometry', stylers: [{ color: '#d9dfd5' }] },
  { featureType: 'poi.park', elementType: 'geometry', stylers: [{ color: '#cbdacb' }] },
  { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#ffffff' }] },
  { featureType: 'road.arterial', elementType: 'geometry', stylers: [{ color: '#f4eec8' }] },
  { featureType: 'road.highway', elementType: 'geometry', stylers: [{ color: '#efcf44' }] },
  { featureType: 'transit', elementType: 'geometry', stylers: [{ color: '#d5d7d1' }] },
  { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#bdced0' }] },
];

function regionFor(destination?: string): Region {
  const normalized = (destination ?? '').toLocaleLowerCase('vi');
  const found = Object.entries(fallbackRegions).find(([key]) => normalized.includes(key));
  return found?.[1] ?? { latitude: 16.0544, longitude: 108.2022, latitudeDelta: 5.6, longitudeDelta: 5.6 };
}

function PhotoMarker({ place, destination, selected, onPress }: { place: PlaceSuggestion; destination: string; selected: boolean; onPress: () => void }) {
  const photo = usePlaceImage(place.name, destination, place.imageUrl);
  const [tracksViewChanges, setTracksViewChanges] = useState(true);

  useEffect(() => {
    setTracksViewChanges(true);
    if (!photo.loading) {
      const timer = setTimeout(() => setTracksViewChanges(false), 500);
      return () => clearTimeout(timer);
    }
  }, [photo.loading, photo.uri, selected]);

  return (
    <Marker
      coordinate={{ latitude: Number(place.latitude), longitude: Number(place.longitude) }}
      anchor={{ x: 0.5, y: 0.95 }}
      tracksViewChanges={tracksViewChanges}
      onPress={onPress}
    >
      <View style={[styles.photoMarker, selected && styles.photoMarkerActive]}>
        <Image source={photo.source} style={styles.markerPhoto} resizeMode="cover" onLoad={() => setTracksViewChanges(false)} />
        {!photo.uri && photo.loading && <View style={styles.markerPlaceholder}><Ionicons name="image-outline" size={14} color={palette.muted} /></View>}
        <View style={[styles.markerPointer, selected && styles.markerPointerActive]} />
      </View>
    </Marker>
  );
}

export default function MapScreen() {
  const { activeTrip, trips, setActiveTripId } = useTravel();
  const mapRef = useRef<MapView>(null);
  const placeCardMotion = useRef(new Animated.Value(1)).current;
  const [places, setPlaces] = useState<PlaceSuggestion[]>([]);
  const [selected, setSelected] = useState<PlaceSuggestion | null>(null);
  const [selectedDay, setSelectedDay] = useState(1);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const selectedPhoto = usePlaceImage(selected?.name, activeTrip?.destination, selected?.imageUrl);

  async function loadPlaces(note = '') {
    if (!activeTrip) return;
    setLoading(true);
    setError('');
    try {
      const raw = await apiRequest<string>('/api/v1/ai/suggest-places', {
        method: 'POST',
        body: JSON.stringify({
          city: activeTrip.destination,
          type: null,
          specialNote: note || `Địa điểm nổi bật phù hợp ngày ${selectedDay} của hành trình, tối ưu di chuyển`,
          count: 6,
        }),
      });
      const response = parseJsonData<PlaceSuggestionResponse>(raw);
      const parsed = response.suggestions.filter((place) => Number.isFinite(Number(place.latitude)) && Number.isFinite(Number(place.longitude)));
      setPlaces(parsed);
      setSelected(parsed[0] ?? null);
      if (parsed.length) {
        requestAnimationFrame(() => mapRef.current?.fitToCoordinates(
          parsed.map((place) => ({ latitude: Number(place.latitude), longitude: Number(place.longitude) })),
          { edgePadding: { top: 190, right: 52, bottom: 245, left: 52 }, animated: true },
        ));
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Chưa thể tải địa điểm.');
      setPlaces([]);
      setSelected(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setSelectedDay(1);
    if (activeTrip) mapRef.current?.animateToRegion(regionFor(activeTrip.destination), 450);
    loadPlaces().catch(() => undefined);
    // Chỉ tải lại khi chuyển sang một chuyến đi khác.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTrip?.id]);

  useEffect(() => {
    if (!selected) return;
    placeCardMotion.setValue(0);
    Animated.spring(placeCardMotion, {
      toValue: 1,
      damping: 18,
      stiffness: 170,
      mass: 0.72,
      useNativeDriver: true,
    }).start();
  }, [placeCardMotion, selected]);

  function focusPlace(place: PlaceSuggestion) {
    setSelected(place);
    mapRef.current?.animateCamera({ center: { latitude: Number(place.latitude), longitude: Number(place.longitude) }, zoom: 15 }, { duration: 650 });
  }

  function stepPlace(direction: number) {
    if (!places.length || !selected) return;
    const currentIndex = places.findIndex((place) => place.name === selected.name);
    focusPlace(places[(currentIndex + direction + places.length) % places.length]);
  }

  function switchTrip() {
    if (trips.length < 2 || !activeTrip) return;
    const currentIndex = trips.findIndex((trip) => trip.id === activeTrip.id);
    setActiveTripId(trips[(currentIndex + 1) % trips.length].id);
  }

  if (!activeTrip) return <AppScreen><View style={styles.emptyTop}><Brand compact /><Text style={styles.emptyHeading}>Bản đồ hành trình</Text></View><EmptyState icon="navigate-outline" title="Chưa chọn chuyến đi" message="Tạo hoặc chọn một chuyến đi để mở bản đồ địa điểm có ngữ cảnh." /></AppScreen>;

  const dayCount = Math.max(1, Math.min(activeTrip.durationDays, 7));

  return (
    <AppScreen scroll={false} style={styles.content}>
      <View style={styles.topbar}>
        <Brand compact />
        <View style={styles.topActions}>
          <Pressable onPress={() => loadPlaces(query)} style={styles.roundButton}><Ionicons name="sparkles-outline" size={18} color={palette.ink} /></Pressable>
          <Pressable onPress={() => mapRef.current?.animateToRegion(regionFor(activeTrip.destination), 500)} style={styles.roundButton}><Ionicons name="locate-outline" size={19} color={palette.ink} /></Pressable>
        </View>
      </View>

      <View style={styles.mapShell}>
        <MapView
          ref={mapRef}
          provider={PROVIDER_DEFAULT}
          style={styles.map}
          initialRegion={regionFor(activeTrip.destination)}
          customMapStyle={lightMapStyle}
          toolbarEnabled={false}
          showsCompass={false}
          showsUserLocation={false}
          showsPointsOfInterest={false}
        >
          {places.map((place, index) => (
            <PhotoMarker
              key={`${place.name}-${index}`}
              place={place}
              destination={activeTrip.destination}
              selected={selected?.name === place.name}
              onPress={() => focusPlace(place)}
            />
          ))}
        </MapView>

        <View style={styles.routeHeader}>
          <View style={styles.routeRow}>
            <View style={styles.routeCopy}>
              <Text style={styles.routeEyebrow}>AI TRAVEL MAP</Text>
              <Text style={styles.routeTitle}>{activeTrip.destination}</Text>
              <Text style={styles.routeMeta}>{formatDate(activeTrip.startDate)} — {activeTrip.durationDays} ngày</Text>
            </View>
            <Pressable onPress={switchTrip} disabled={trips.length < 2} style={styles.switchButton}>
              <Ionicons name={trips.length > 1 ? 'swap-horizontal' : 'map-outline'} size={18} color={palette.white} />
            </Pressable>
          </View>
          <ScrollView horizontal style={styles.dayScroller} contentContainerStyle={styles.dayRail} showsHorizontalScrollIndicator={false}>
            {Array.from({ length: dayCount }, (_, index) => index + 1).map((day) => (
              <Pressable key={day} onPress={() => setSelectedDay(day)} style={[styles.dayChip, selectedDay === day && styles.dayChipActive]}>
                <Text style={[styles.dayNumber, selectedDay === day && styles.dayNumberActive]}>{day}</Text>
                <Text style={[styles.dayLabel, selectedDay === day && styles.dayLabelActive]}>Ngày</Text>
              </Pressable>
            ))}
          </ScrollView>
        </View>

        <View style={styles.searchCard}>
          <Ionicons name="search" size={18} color={palette.ink} />
          <TextInput value={query} onChangeText={setQuery} onSubmitEditing={() => loadPlaces(query)} placeholder="Ăn ngon, chụp ảnh, đi cùng gia đình..." placeholderTextColor="#777D77" style={styles.searchInput} />
          <Pressable onPress={() => loadPlaces(query)} style={styles.searchButton}>{loading ? <Ionicons name="hourglass-outline" size={17} color={palette.ink} /> : <Ionicons name="arrow-forward" size={18} color={palette.ink} />}</Pressable>
        </View>

        {loading && places.length === 0 && <View style={styles.mapLoading}><LoadingState label="AI đang đặt địa điểm lên bản đồ..." /></View>}
        {error ? <View style={styles.errorCard}><Ionicons name="alert-circle-outline" size={17} color={palette.danger} /><Text style={styles.errorText}>{error}</Text><Pressable onPress={() => loadPlaces(query)}><Text style={styles.retryText}>Thử lại</Text></Pressable></View> : null}

        {selected && (
          <Animated.View style={[styles.placeCard, {
            opacity: placeCardMotion,
            transform: [{ translateY: placeCardMotion.interpolate({ inputRange: [0, 1], outputRange: [24, 0] }) }, { scale: placeCardMotion.interpolate({ inputRange: [0, 1], outputRange: [0.97, 1] }) }],
          }]}>
            <View style={styles.placePhotoWrap}>
              <Image source={selectedPhoto.source} style={styles.placePhoto} resizeMode="cover" />
              <LinearGradient colors={['rgba(16,19,15,0.02)', 'rgba(16,19,15,0.62)']} style={StyleSheet.absoluteFill} />
              <View style={styles.photoTopline}>
                <View style={styles.categoryPill}><Text style={styles.categoryText}>{selected.category ?? `GỢI Ý NGÀY ${selectedDay}`}</Text></View>
                <View style={styles.placeCounterPill}><Text style={styles.placeCounter}>{Math.max(1, places.findIndex((place) => place.name === selected.name) + 1)}/{places.length}</Text></View>
              </View>
              <View style={styles.photoNavigation}>
                <Pressable onPress={() => stepPlace(-1)} style={styles.photoArrow}><Ionicons name="chevron-back" size={17} color={palette.ink} /></Pressable>
                <Pressable onPress={() => stepPlace(1)} style={styles.photoArrow}><Ionicons name="chevron-forward" size={17} color={palette.ink} /></Pressable>
              </View>
              <Text style={styles.photoTitle} numberOfLines={1}>{selected.name}</Text>
            </View>
            <View style={styles.placeContent}>
              <View style={styles.placeCopy}>
                <Text style={styles.placeReason} numberOfLines={2}>{selected.reason ?? selected.description ?? `Một điểm dừng đáng cân nhắc tại ${activeTrip.destination}.`}</Text>
                <View style={styles.placeFooter}>
                  <View style={styles.placeFact}><Ionicons name="location-outline" size={13} color={palette.forest} /><Text style={styles.placeFactText} numberOfLines={1}>{selected.address ?? activeTrip.destination}</Text></View>
                  <Text style={styles.cost}>OpenStreetMap</Text>
                </View>
              </View>
              <Pressable onPress={() => Linking.openURL(selected.mapUrl ?? `https://www.openstreetmap.org/?mlat=${selected.latitude}&mlon=${selected.longitude}`)} style={styles.navigateButton}><Ionicons name="arrow-up-outline" size={19} color={palette.white} /></Pressable>
            </View>
          </Animated.View>
        )}
      </View>
    </AppScreen>
  );
}

const styles = StyleSheet.create({
  content: { paddingTop: 8, paddingBottom: 106, gap: 11 },
  topbar: { minHeight: 42, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  topActions: { flexDirection: 'row', gap: 7 },
  roundButton: { width: 38, height: 38, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(247,247,244,0.92)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.8)', borderRadius: 13 },
  mapShell: { flex: 1, minHeight: 0, overflow: 'hidden', backgroundColor: '#D6D8D3', borderWidth: 5, borderColor: 'rgba(247,247,244,0.9)', borderRadius: 29, ...shadows.dark },
  map: { flex: 1 },
  photoMarker: { width: 44, height: 44, padding: 3, backgroundColor: palette.white, borderWidth: 2, borderColor: palette.white, borderRadius: 22, ...shadows.card },
  photoMarkerActive: { width: 58, height: 58, padding: 3, borderWidth: 4, borderColor: palette.lime, borderRadius: 29 },
  markerPhoto: { width: '100%', height: '100%', backgroundColor: palette.sage, borderRadius: 999 },
  markerPlaceholder: { ...StyleSheet.absoluteFillObject, alignItems: 'center', justifyContent: 'center', margin: 3, backgroundColor: palette.sage, borderRadius: 999 },
  markerPointer: { width: 9, height: 9, position: 'absolute', left: '50%', bottom: -5, marginLeft: -3, backgroundColor: palette.white, transform: [{ rotate: '45deg' }] },
  markerPointerActive: { width: 11, height: 11, bottom: -6, marginLeft: -3, backgroundColor: palette.lime },
  routeHeader: { position: 'absolute', top: 9, left: 9, right: 9, padding: 12, paddingBottom: 9, backgroundColor: 'rgba(247,247,244,0.97)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.94)', borderRadius: 22, ...shadows.card },
  routeRow: { minHeight: 52, flexDirection: 'row', alignItems: 'center', gap: 10 },
  routeCopy: { flex: 1 },
  routeEyebrow: { color: palette.forest, fontSize: 7, fontWeight: '900', letterSpacing: 1.2 },
  routeTitle: { marginTop: 3, color: palette.ink, fontSize: 21, fontWeight: '900', letterSpacing: -0.8 },
  routeMeta: { marginTop: 2, color: palette.muted, fontSize: 8 },
  switchButton: { width: 39, height: 39, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.ink, borderRadius: 13 },
  dayScroller: { height: 45, maxHeight: 45, flexGrow: 0 },
  dayRail: { alignItems: 'center', gap: 7 },
  dayChip: { width: 43, height: 42, alignItems: 'center', justifyContent: 'center', backgroundColor: '#E4E6E1', borderRadius: 14 },
  dayChipActive: { backgroundColor: palette.lime },
  dayNumber: { color: palette.ink, fontSize: 11, lineHeight: 13, fontWeight: '900' },
  dayNumberActive: { color: palette.ink },
  dayLabel: { color: palette.muted, fontSize: 6 },
  dayLabelActive: { color: palette.ink },
  searchCard: { height: 52, position: 'absolute', top: 127, left: 12, right: 12, paddingHorizontal: 7, flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: 'rgba(247,247,244,0.96)', borderWidth: 1, borderColor: palette.white, borderRadius: 17, ...shadows.card },
  searchInput: { flex: 1, color: palette.ink, fontSize: 10, fontWeight: '700' },
  searchButton: { width: 38, height: 38, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 12 },
  mapLoading: { position: 'absolute', top: 180, left: 12, right: 12, bottom: 225, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(229,230,226,0.82)', borderRadius: 22 },
  errorCard: { position: 'absolute', top: 187, left: 12, right: 12, padding: 11, flexDirection: 'row', alignItems: 'center', gap: 7, backgroundColor: '#FFF0EC', borderRadius: 14 },
  errorText: { flex: 1, color: palette.danger, fontSize: 8, lineHeight: 12 },
  retryText: { color: palette.danger, fontSize: 8, fontWeight: '900' },
  placeCard: { height: 220, maxHeight: 220, position: 'absolute', left: 11, right: 11, bottom: 11, overflow: 'hidden', backgroundColor: 'rgba(247,247,244,0.99)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.94)', borderRadius: 24, ...shadows.dark },
  placePhotoWrap: { height: 128, overflow: 'hidden', backgroundColor: palette.sage },
  placePhoto: { width: '100%', height: '100%' },
  photoTopline: { position: 'absolute', top: 10, left: 10, right: 10, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  categoryPill: { maxWidth: 145, paddingHorizontal: 9, paddingVertical: 6, backgroundColor: palette.lime, borderRadius: radii.pill },
  categoryText: { color: palette.ink, fontSize: 6, fontWeight: '900' },
  placeCounterPill: { minWidth: 34, paddingHorizontal: 8, paddingVertical: 6, alignItems: 'center', backgroundColor: 'rgba(16,19,15,0.68)', borderRadius: radii.pill },
  placeCounter: { color: palette.white, fontSize: 7, fontWeight: '900' },
  photoNavigation: { position: 'absolute', right: 10, bottom: 9, flexDirection: 'row', gap: 6 },
  photoArrow: { width: 31, height: 31, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(247,247,244,0.94)', borderRadius: 11 },
  photoTitle: { position: 'absolute', left: 12, right: 90, bottom: 10, color: palette.white, fontSize: 17, fontWeight: '900', letterSpacing: -0.5 },
  placeContent: { height: 92, padding: 11, flexDirection: 'row', alignItems: 'center', gap: 10 },
  placeCopy: { flex: 1, minWidth: 0 },
  placeReason: { minHeight: 25, color: palette.inkSoft, fontSize: 8, lineHeight: 12 },
  placeFooter: { marginTop: 7, paddingTop: 6, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 5, borderTopWidth: 1, borderTopColor: palette.line },
  placeFact: { flex: 1, minWidth: 0, flexDirection: 'row', alignItems: 'center', gap: 3 },
  placeFactText: { flex: 1, color: palette.muted, fontSize: 7 },
  cost: { color: palette.forest, fontSize: 7, fontWeight: '900' },
  navigateButton: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.forest, borderRadius: 15 },
  emptyTop: { gap: 28 },
  emptyHeading: { color: palette.ink, fontSize: 30, fontWeight: '900', letterSpacing: -1.2 },
});
