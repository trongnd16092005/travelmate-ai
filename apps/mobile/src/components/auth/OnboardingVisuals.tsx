import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useEffect, useRef } from 'react';
import { Animated, Image, StyleSheet, Text, View } from 'react-native';

import { palette, radii, shadows, tripImages } from '@/constants/design';

type VisualProps = {
  height: number;
};

function useFloatAnimation(distance = 8) {
  const value = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(value, { toValue: 1, duration: 1500, useNativeDriver: true }),
        Animated.timing(value, { toValue: 0, duration: 1500, useNativeDriver: true }),
      ]),
    );
    animation.start();
    return () => animation.stop();
  }, [value]);

  return {
    transform: [
      {
        translateY: value.interpolate({ inputRange: [0, 1], outputRange: [0, -distance] }),
      },
    ],
  };
}

export function WelcomeJourneyVisual({ height }: VisualProps) {
  const floatStyle = useFloatAnimation(10);
  const planeStyle = useFloatAnimation(6);

  return (
    <View style={[styles.canvas, { height }]}>
      <View style={styles.sun} />
      <View style={[styles.cloud, styles.cloudLeft]}>
        <View style={styles.cloudPuffSmall} />
        <View style={styles.cloudPuffLarge} />
      </View>
      <View style={[styles.cloud, styles.cloudRight]}>
        <View style={styles.cloudPuffSmall} />
        <View style={styles.cloudPuffLarge} />
      </View>

      <View style={[styles.hill, styles.hillBack]} />
      <View style={[styles.hill, styles.hillFront]} />
      <View style={styles.routeLine} />

      <Animated.View style={[styles.planeBadge, planeStyle]}>
        <Ionicons name="airplane" size={18} color={palette.white} />
      </Animated.View>

      <Animated.View style={[styles.balloonWrap, floatStyle]}>
        <LinearGradient colors={['#F6D232', '#E7B81A']} style={styles.balloon}>
          <View style={styles.balloonStripe} />
          <View style={[styles.balloonStripe, styles.balloonStripeRight]} />
        </LinearGradient>
        <View style={styles.balloonRope} />
        <View style={styles.balloonBasket} />
      </Animated.View>

      <View style={styles.traveler}>
        <View style={styles.travelerHead} />
        <View style={styles.travelerHat} />
        <View style={styles.travelerBody}>
          <Ionicons name="map-outline" size={26} color={palette.limeSoft} />
        </View>
        <View style={styles.travelerLegLeft} />
        <View style={styles.travelerLegRight} />
      </View>

      <View style={styles.pinWrap}>
        <Ionicons name="location" size={34} color={palette.lime} />
      </View>
      <View style={styles.tripTag}>
        <View style={styles.tripTagIcon}><Ionicons name="compass" size={14} color={palette.white} /></View>
        <View>
          <Text style={styles.tripTagEyebrow}>HÀNH TRÌNH TIẾP THEO</Text>
          <Text style={styles.tripTagTitle}>Việt Nam</Text>
        </View>
      </View>
    </View>
  );
}

export function DestinationDeckVisual({ height }: VisualProps) {
  const floatStyle = useFloatAnimation(7);

  return (
    <View style={[styles.destinationCanvas, { height }]}>
      <View style={styles.destinationGrid}>
        <View style={styles.largeDestinationCard}>
          <Image source={tripImages.hue} style={styles.destinationImage} resizeMode="cover" />
          <LinearGradient colors={['transparent', 'rgba(8,12,9,0.76)']} style={StyleSheet.absoluteFill} />
          <View style={styles.photoLabel}>
            <Text style={styles.photoEyebrow}>DI SẢN</Text>
            <Text style={styles.photoTitle}>Huế</Text>
            <Text style={styles.photoMeta}>4 ngày • văn hoá</Text>
          </View>
        </View>

        <View style={styles.sideCards}>
          <View style={styles.countCard}>
            <View style={styles.countIcon}><Ionicons name="map-outline" size={19} color={palette.forest} /></View>
            <Text style={styles.countNumber}>23</Text>
            <Text style={styles.countMeta}>điểm đến{`\n`}đang chờ</Text>
          </View>
          <View style={styles.smallDestinationCard}>
            <Image source={tripImages.mountain} style={styles.destinationImage} resizeMode="cover" />
            <LinearGradient colors={['transparent', 'rgba(8,12,9,0.78)']} style={StyleSheet.absoluteFill} />
            <View style={styles.smallPhotoLabel}>
              <Text style={styles.photoEyebrow}>PHIÊU LƯU</Text>
              <Text style={styles.smallPhotoTitle}>Hà Giang</Text>
            </View>
          </View>
        </View>
      </View>

      <Animated.View style={[styles.discoveryPill, floatStyle]}>
        <View style={styles.discoveryIcon}><Ionicons name="sparkles" size={17} color={palette.ink} /></View>
        <View style={styles.discoveryCopy}>
          <Text style={styles.discoveryTitle}>Đúng nơi, đúng nhịp</Text>
          <Text style={styles.discoveryMeta}>Gợi ý được cá nhân hoá cho bạn</Text>
        </View>
        <Ionicons name="arrow-forward" size={17} color={palette.ink} />
      </Animated.View>
    </View>
  );
}

export function AiMapVisual({ height }: VisualProps) {
  const floatStyle = useFloatAnimation(8);

  return (
    <View style={[styles.mapCanvas, { height }]}>
      <View style={styles.mapGrid}>
        <View style={[styles.road, styles.roadOne]} />
        <View style={[styles.road, styles.roadTwo]} />
        <View style={[styles.road, styles.roadThree]} />
        <View style={[styles.park, styles.parkOne]} />
        <View style={[styles.park, styles.parkTwo]} />
      </View>
      <View style={[styles.routeSegment, styles.routeSegmentOne]} />
      <View style={[styles.routeSegment, styles.routeSegmentTwo]} />
      <View style={[styles.routeSegment, styles.routeSegmentThree]} />
      <View style={[styles.mapMarker, styles.mapMarkerStart]}><Ionicons name="cafe" size={13} color={palette.ink} /></View>
      <View style={[styles.mapMarker, styles.mapMarkerEnd]}><Ionicons name="camera" size={13} color={palette.ink} /></View>

      <View style={styles.mapHeader}>
        <View style={styles.mapHeaderIcon}><Ionicons name="navigate" size={16} color={palette.white} /></View>
        <View>
          <Text style={styles.mapHeaderEyebrow}>LỊCH TRÌNH AI</Text>
          <Text style={styles.mapHeaderTitle}>Một ngày ở Huế</Text>
        </View>
        <View style={styles.onlineDot} />
      </View>

      <Animated.View style={[styles.chatCard, floatStyle]}>
        <View style={styles.aiAvatar}><Ionicons name="sparkles" size={17} color={palette.ink} /></View>
        <View style={styles.chatCopy}>
          <Text style={styles.chatTitle}>TravelMate AI</Text>
          <Text style={styles.chatText}>Mình đã nối Đại Nội, món Huế và điểm ngắm hoàng hôn thành một tuyến gọn.</Text>
        </View>
      </Animated.View>

      <View style={styles.placeCard}>
        <Image source={tripImages.heritage} style={styles.placeThumb} resizeMode="cover" />
        <View style={styles.placeCopy}>
          <Text style={styles.placeTitle}>Trải nghiệm địa phương</Text>
          <Text style={styles.placeMeta}>3 điểm • 4 giờ 20 phút</Text>
        </View>
        <View style={styles.placeArrow}><Ionicons name="arrow-forward" size={16} color={palette.ink} /></View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  canvas: {
    overflow: 'hidden',
    backgroundColor: '#DCE6D5',
    borderRadius: 34,
    borderWidth: 1,
    borderColor: 'rgba(16,19,15,0.07)',
  },
  sun: { position: 'absolute', top: 26, right: 28, width: 62, height: 62, borderRadius: 31, backgroundColor: palette.limeSoft },
  cloud: { position: 'absolute', height: 24, flexDirection: 'row', alignItems: 'flex-end' },
  cloudLeft: { top: 72, left: 26 },
  cloudRight: { top: 112, right: 30 },
  cloudPuffSmall: { width: 25, height: 13, borderTopLeftRadius: 18, borderTopRightRadius: 18, backgroundColor: 'rgba(255,255,255,0.82)' },
  cloudPuffLarge: { width: 34, height: 21, marginLeft: -7, borderTopLeftRadius: 22, borderTopRightRadius: 22, backgroundColor: 'rgba(255,255,255,0.92)' },
  hill: { position: 'absolute', bottom: -82, borderTopLeftRadius: 180, borderTopRightRadius: 180 },
  hillBack: { left: -70, width: 310, height: 230, backgroundColor: '#94C39A', transform: [{ rotate: '8deg' }] },
  hillFront: { right: -68, width: 270, height: 185, backgroundColor: palette.forest, transform: [{ rotate: '-8deg' }] },
  routeLine: { position: 'absolute', left: 126, bottom: 60, width: 140, height: 76, borderWidth: 3, borderColor: palette.lime, borderLeftColor: 'transparent', borderBottomColor: 'transparent', borderRadius: 72, transform: [{ rotate: '18deg' }] },
  planeBadge: { position: 'absolute', top: 50, left: 28, width: 46, height: 46, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.forest, borderRadius: 23, ...shadows.card },
  balloonWrap: { position: 'absolute', top: 34, left: '42%', width: 86, alignItems: 'center' },
  balloon: { width: 72, height: 91, overflow: 'hidden', borderRadius: 40 },
  balloonStripe: { position: 'absolute', left: 18, top: -2, width: 12, height: 98, borderRadius: 12, backgroundColor: palette.forest },
  balloonStripeRight: { left: 43 },
  balloonRope: { width: 26, height: 13, borderLeftWidth: 1.5, borderRightWidth: 1.5, borderColor: palette.ink },
  balloonBasket: { width: 24, height: 15, backgroundColor: '#C9783D', borderBottomLeftRadius: 4, borderBottomRightRadius: 4 },
  traveler: { position: 'absolute', bottom: 28, left: 42, width: 92, height: 137 },
  travelerHead: { position: 'absolute', top: 0, left: 33, width: 28, height: 28, borderRadius: 14, backgroundColor: '#C78355' },
  travelerHat: { position: 'absolute', top: -6, left: 26, width: 43, height: 12, backgroundColor: palette.lime, borderRadius: 7, transform: [{ rotate: '-8deg' }] },
  travelerBody: { position: 'absolute', top: 24, left: 18, width: 58, height: 69, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.forest, borderRadius: 17 },
  travelerLegLeft: { position: 'absolute', left: 25, bottom: 0, width: 13, height: 49, backgroundColor: palette.ink, borderRadius: 8, transform: [{ rotate: '8deg' }] },
  travelerLegRight: { position: 'absolute', right: 23, bottom: 2, width: 13, height: 51, backgroundColor: palette.ink, borderRadius: 8, transform: [{ rotate: '-14deg' }] },
  pinWrap: { position: 'absolute', right: 29, bottom: 61 },
  tripTag: { position: 'absolute', right: 18, bottom: 17, minWidth: 178, paddingHorizontal: 13, paddingVertical: 11, flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: 'rgba(247,247,244,0.94)', borderRadius: radii.md, ...shadows.card },
  tripTagIcon: { width: 32, height: 32, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.ink, borderRadius: 12 },
  tripTagEyebrow: { color: palette.muted, fontSize: 7, fontWeight: '900', letterSpacing: 0.8 },
  tripTagTitle: { marginTop: 2, color: palette.ink, fontSize: 15, fontWeight: '900' },

  destinationCanvas: { justifyContent: 'center' },
  destinationGrid: { flex: 1, flexDirection: 'row', gap: 10 },
  largeDestinationCard: { flex: 1.07, overflow: 'hidden', borderRadius: 30, backgroundColor: palette.sage },
  sideCards: { flex: 0.83, gap: 10 },
  destinationImage: { width: '100%', height: '100%' },
  photoLabel: { position: 'absolute', left: 16, right: 16, bottom: 18 },
  photoEyebrow: { color: palette.lime, fontSize: 8, fontWeight: '900', letterSpacing: 1 },
  photoTitle: { marginTop: 3, color: palette.white, fontSize: 25, fontWeight: '900', letterSpacing: -1 },
  photoMeta: { marginTop: 3, color: 'rgba(255,255,255,0.73)', fontSize: 9 },
  countCard: { flex: 0.74, padding: 15, justifyContent: 'center', backgroundColor: palette.limeSoft, borderRadius: 28 },
  countIcon: { width: 38, height: 38, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.72)', borderRadius: 19 },
  countNumber: { marginTop: 8, color: palette.ink, fontSize: 34, lineHeight: 36, fontWeight: '900', letterSpacing: -1.5 },
  countMeta: { color: palette.muted, fontSize: 8, lineHeight: 12, fontWeight: '700' },
  smallDestinationCard: { flex: 1.26, overflow: 'hidden', borderRadius: 28, backgroundColor: palette.sage },
  smallPhotoLabel: { position: 'absolute', left: 14, right: 14, bottom: 14 },
  smallPhotoTitle: { marginTop: 3, color: palette.white, fontSize: 17, fontWeight: '900' },
  discoveryPill: { position: 'absolute', left: 16, right: 16, bottom: 16, minHeight: 66, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: 'rgba(247,247,244,0.96)', borderRadius: 22, ...shadows.dark },
  discoveryIcon: { width: 39, height: 39, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 15 },
  discoveryCopy: { flex: 1 },
  discoveryTitle: { color: palette.ink, fontSize: 11, fontWeight: '900' },
  discoveryMeta: { marginTop: 3, color: palette.muted, fontSize: 8 },

  mapCanvas: { overflow: 'hidden', backgroundColor: '#DBDDD8', borderRadius: 34, borderWidth: 1, borderColor: palette.line },
  mapGrid: { ...StyleSheet.absoluteFillObject, backgroundColor: '#DADDD8' },
  road: { position: 'absolute', height: 22, backgroundColor: '#F6F6F2', borderWidth: 1, borderColor: 'rgba(16,19,15,0.05)', borderRadius: 12 },
  roadOne: { top: 97, left: -32, width: 310, transform: [{ rotate: '25deg' }] },
  roadTwo: { top: 194, left: 22, width: 390, transform: [{ rotate: '-16deg' }] },
  roadThree: { top: 95, right: -85, width: 270, transform: [{ rotate: '73deg' }] },
  park: { position: 'absolute', backgroundColor: '#C4D7C5', borderRadius: 42 },
  parkOne: { top: 120, left: -30, width: 148, height: 104, transform: [{ rotate: '-12deg' }] },
  parkTwo: { top: 46, right: 10, width: 105, height: 84, transform: [{ rotate: '13deg' }] },
  routeSegment: { position: 'absolute', height: 3, backgroundColor: palette.lime, borderRadius: 4 },
  routeSegmentOne: { top: 123, left: 51, width: 125, transform: [{ rotate: '25deg' }] },
  routeSegmentTwo: { top: 171, left: 156, width: 93, transform: [{ rotate: '56deg' }] },
  routeSegmentThree: { top: 221, left: 218, width: 82, transform: [{ rotate: '-19deg' }] },
  mapMarker: { position: 'absolute', width: 32, height: 32, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderWidth: 4, borderColor: palette.ink, borderRadius: 16, ...shadows.card },
  mapMarkerStart: { top: 101, left: 40 },
  mapMarkerEnd: { top: 203, right: 41 },
  mapHeader: { position: 'absolute', top: 14, left: 14, right: 14, minHeight: 60, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: palette.ink, borderRadius: 22, ...shadows.dark },
  mapHeaderIcon: { width: 36, height: 36, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.forest, borderRadius: 14 },
  mapHeaderEyebrow: { color: 'rgba(255,255,255,0.52)', fontSize: 7, fontWeight: '900', letterSpacing: 0.8 },
  mapHeaderTitle: { marginTop: 2, color: palette.white, fontSize: 13, fontWeight: '900' },
  onlineDot: { width: 9, height: 9, marginLeft: 'auto', backgroundColor: palette.lime, borderRadius: 5 },
  chatCard: { position: 'absolute', top: 93, right: 15, width: '72%', padding: 12, flexDirection: 'row', alignItems: 'flex-start', gap: 9, backgroundColor: 'rgba(247,247,244,0.96)', borderRadius: 21, ...shadows.dark },
  aiAvatar: { width: 34, height: 34, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 13 },
  chatCopy: { flex: 1 },
  chatTitle: { color: palette.ink, fontSize: 10, fontWeight: '900' },
  chatText: { marginTop: 3, color: palette.muted, fontSize: 8, lineHeight: 12 },
  placeCard: { position: 'absolute', left: 15, right: 15, bottom: 15, minHeight: 75, padding: 8, flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: palette.paper, borderRadius: 23, ...shadows.dark },
  placeThumb: { width: 60, height: 59, borderRadius: 17 },
  placeCopy: { flex: 1 },
  placeTitle: { color: palette.ink, fontSize: 10, fontWeight: '900' },
  placeMeta: { marginTop: 4, color: palette.muted, fontSize: 8 },
  placeArrow: { width: 36, height: 36, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 14 },
});
