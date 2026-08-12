import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useRef, useState } from 'react';
import {
  Animated,
  NativeScrollEvent,
  NativeSyntheticEvent,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  AiMapVisual,
  DestinationDeckVisual,
  WelcomeJourneyVisual,
} from '@/components/auth/OnboardingVisuals';
import { Brand } from '@/components/ui';
import { palette, radii, shadows } from '@/constants/design';

const SLIDES = [
  {
    id: 'welcome',
    eyebrow: 'CHÀO MỪNG ĐẾN VỚI',
    title: 'TravelMate',
    accent: 'đi theo nhịp của bạn.',
    description: 'Khám phá nơi đáng đến và giữ từng bước của chuyến đi thật nhẹ nhàng.',
  },
  {
    id: 'discover',
    eyebrow: 'KHÁM PHÁ CÓ CHỌN LỌC',
    title: 'Đi đúng nơi,',
    accent: 'đúng cảm hứng.',
    description: 'Điểm đến, lịch trình và ngân sách được gom vào một trải nghiệm dễ dùng.',
  },
  {
    id: 'companion',
    eyebrow: 'AI HIỂU CẢ CHUYẾN ĐI',
    title: 'Hỏi một câu,',
    accent: 'thấy cả hành trình.',
    description: 'TravelMate AI nối lịch trình với bản đồ để bạn luôn biết mình nên đi đâu tiếp.',
  },
] as const;

export default function WelcomeScreen() {
  const { width, height } = useWindowDimensions();
  const scrollX = useRef(new Animated.Value(0)).current;
  const scrollRef = useRef<ScrollView>(null);
  const [activePage, setActivePage] = useState(0);
  const visualHeight = Math.max(250, Math.min(338, height * 0.36));

  function goToPage(page: number) {
    const nextPage = Math.max(0, Math.min(SLIDES.length - 1, page));
    scrollRef.current?.scrollTo({ x: nextPage * width, animated: true });
    setActivePage(nextPage);
  }

  function handleMomentumEnd(event: NativeSyntheticEvent<NativeScrollEvent>) {
    const page = Math.round(event.nativeEvent.contentOffset.x / width);
    setActivePage(page);
  }

  return (
    <View style={styles.screen}>
      <StatusBar style="dark" />
      <View style={styles.decorCircle} />
      <View style={styles.decorDot} />
      <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
        <View style={styles.header}>
          <Brand compact />
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Bỏ qua phần giới thiệu"
            onPress={() => router.replace('/(auth)/login')}
            style={({ pressed }) => [styles.skipButton, pressed && styles.pressed]}
          >
            <Text style={styles.skipText}>Bỏ qua</Text>
            <Ionicons name="arrow-forward" size={14} color={palette.ink} />
          </Pressable>
        </View>

        <Animated.ScrollView
          ref={scrollRef}
          horizontal
          pagingEnabled
          bounces={false}
          decelerationRate="fast"
          showsHorizontalScrollIndicator={false}
          scrollEventThrottle={16}
          onMomentumScrollEnd={handleMomentumEnd}
          onScroll={Animated.event(
            [{ nativeEvent: { contentOffset: { x: scrollX } } }],
            { useNativeDriver: true },
          )}
        >
          {SLIDES.map((slide, index) => (
            <OnboardingSlide
              key={slide.id}
              index={index}
              scrollX={scrollX}
              screenWidth={width}
              visualHeight={visualHeight}
              {...slide}
            />
          ))}
        </Animated.ScrollView>

        <View style={styles.footer}>
          <View style={styles.pagination} accessibilityLabel={`Trang ${activePage + 1} trên ${SLIDES.length}`}>
            {SLIDES.map((slide, index) => {
              const inputRange = [(index - 1) * width, index * width, (index + 1) * width];
              const scaleX = scrollX.interpolate({ inputRange, outputRange: [1, 2.3, 1], extrapolate: 'clamp' });
              const opacity = scrollX.interpolate({ inputRange, outputRange: [0.22, 1, 0.22], extrapolate: 'clamp' });
              return (
                <Pressable key={slide.id} accessibilityRole="button" accessibilityLabel={`Đến trang ${index + 1}`} onPress={() => goToPage(index)} style={styles.dotHitbox}>
                  <Animated.View style={[styles.pageDot, { opacity, transform: [{ scaleX }] }]} />
                </Pressable>
              );
            })}
          </View>

          {activePage < SLIDES.length - 1 ? (
            <>
              <AnimatedAction label="Tiếp tục" icon="arrow-forward" onPress={() => goToPage(activePage + 1)} />
              <View style={styles.authMenu}>
                <Text style={styles.authPrompt}>Đi ngay?</Text>
                <Pressable onPress={() => router.push('/(auth)/login')} style={({ pressed }) => [styles.authMenuItem, pressed && styles.pressed]}>
                  <Ionicons name="log-in-outline" size={15} color={palette.forest} />
                  <Text style={styles.authMenuText}>Đăng nhập</Text>
                </Pressable>
                <View style={styles.menuDivider} />
                <Pressable onPress={() => router.push('/(auth)/register')} style={({ pressed }) => [styles.authMenuItem, pressed && styles.pressed]}>
                  <Text style={styles.authMenuText}>Đăng ký</Text>
                </Pressable>
              </View>
            </>
          ) : (
            <View style={styles.finalActions}>
              <AnimatedAction label="Đăng nhập" icon="arrow-forward" onPress={() => router.push('/(auth)/login')} />
              <AnimatedAction label="Đăng ký miễn phí" icon="person-add-outline" variant="secondary" onPress={() => router.push('/(auth)/register')} />
            </View>
          )}
        </View>
      </SafeAreaView>
    </View>
  );
}

type SlideProps = (typeof SLIDES)[number] & {
  index: number;
  scrollX: Animated.Value;
  screenWidth: number;
  visualHeight: number;
};

function OnboardingSlide({ index, scrollX, screenWidth, visualHeight, eyebrow, title, accent, description }: SlideProps) {
  const inputRange = [(index - 1) * screenWidth, index * screenWidth, (index + 1) * screenWidth];
  const opacity = scrollX.interpolate({ inputRange, outputRange: [0.22, 1, 0.22], extrapolate: 'clamp' });
  const translateY = scrollX.interpolate({ inputRange, outputRange: [18, 0, 18], extrapolate: 'clamp' });
  const scale = scrollX.interpolate({ inputRange, outputRange: [0.92, 1, 0.92], extrapolate: 'clamp' });
  const Visual = index === 0 ? WelcomeJourneyVisual : index === 1 ? DestinationDeckVisual : AiMapVisual;

  return (
    <View style={[styles.slide, { width: screenWidth }]}>
      <Animated.View style={[styles.copy, { opacity, transform: [{ translateY }] }]}>
        <Text style={styles.eyebrow}>{eyebrow}</Text>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.accent}>{accent}</Text>
      </Animated.View>
      <Animated.View style={[styles.visualWrap, { opacity, transform: [{ scale }] }]}>
        <Visual height={visualHeight} />
      </Animated.View>
      <Animated.View style={{ opacity, transform: [{ translateY }] }}>
        <Text style={styles.description}>{description}</Text>
        <View style={styles.swipeHint}>
          <Ionicons name="swap-horizontal" size={15} color={palette.forest} />
          <Text style={styles.swipeHintText}>Vuốt để khám phá</Text>
        </View>
      </Animated.View>
    </View>
  );
}

function AnimatedAction({
  label,
  icon,
  onPress,
  variant = 'primary',
}: {
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  onPress: () => void;
  variant?: 'primary' | 'secondary';
}) {
  const scale = useRef(new Animated.Value(1)).current;

  function pressIn() {
    Animated.timing(scale, { toValue: 0.975, duration: 90, useNativeDriver: true }).start();
  }

  function pressOut() {
    Animated.spring(scale, { toValue: 1, damping: 14, stiffness: 210, useNativeDriver: true }).start();
  }

  return (
    <Animated.View style={{ transform: [{ scale }] }}>
      <Pressable
        accessibilityRole="button"
        onPress={onPress}
        onPressIn={pressIn}
        onPressOut={pressOut}
        style={[styles.actionButton, variant === 'secondary' && styles.actionSecondary]}
      >
        <Text style={[styles.actionLabel, variant === 'secondary' && styles.actionLabelSecondary]}>{label}</Text>
        <View style={[styles.actionIcon, variant === 'secondary' && styles.actionIconSecondary]}>
          <Ionicons name={icon} size={16} color={variant === 'secondary' ? palette.ink : palette.white} />
        </View>
      </Pressable>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.cream },
  safe: { flex: 1 },
  decorCircle: { position: 'absolute', top: -98, right: -89, width: 264, height: 264, backgroundColor: 'rgba(242,206,32,0.13)', borderRadius: 132 },
  decorDot: { position: 'absolute', left: -31, bottom: 96, width: 96, height: 96, backgroundColor: 'rgba(61,142,88,0.09)', borderRadius: 48 },
  header: { minHeight: 62, paddingHorizontal: 22, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  skipButton: { minHeight: 40, paddingHorizontal: 13, flexDirection: 'row', alignItems: 'center', gap: 5, backgroundColor: 'rgba(247,247,244,0.82)', borderWidth: 1, borderColor: palette.line, borderRadius: radii.pill },
  skipText: { color: palette.ink, fontSize: 10, fontWeight: '900' },
  pressed: { opacity: 0.62 },
  slide: { paddingHorizontal: 22, paddingTop: 6, paddingBottom: 6 },
  copy: { marginBottom: 15 },
  eyebrow: { color: palette.forest, fontSize: 8, fontWeight: '900', letterSpacing: 1.45 },
  title: { marginTop: 7, color: palette.ink, fontSize: 35, lineHeight: 38, fontWeight: '900', letterSpacing: -1.7 },
  accent: { alignSelf: 'flex-start', marginTop: 2, paddingHorizontal: 8, paddingVertical: 2, color: palette.white, fontSize: 27, lineHeight: 32, fontWeight: '900', fontStyle: 'italic', letterSpacing: -1.2, backgroundColor: palette.forest, transform: [{ rotate: '-1deg' }] },
  visualWrap: { flex: 1, justifyContent: 'center' },
  description: { marginTop: 14, paddingHorizontal: 4, color: palette.muted, fontSize: 11, lineHeight: 18, textAlign: 'center' },
  swipeHint: { minHeight: 26, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 5 },
  swipeHintText: { color: palette.forest, fontSize: 8, fontWeight: '800' },
  footer: { minHeight: 166, paddingHorizontal: 22, paddingBottom: 5 },
  pagination: { height: 30, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 3 },
  dotHitbox: { width: 28, height: 28, alignItems: 'center', justifyContent: 'center' },
  pageDot: { width: 10, height: 5, backgroundColor: palette.forest, borderRadius: 3 },
  actionButton: { height: 56, paddingLeft: 20, paddingRight: 9, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: palette.forest, borderRadius: 20, ...shadows.card },
  actionSecondary: { backgroundColor: palette.paper, borderWidth: 1, borderColor: palette.line },
  actionLabel: { color: palette.white, fontSize: 12, fontWeight: '900' },
  actionLabelSecondary: { color: palette.ink },
  actionIcon: { width: 39, height: 39, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(16,19,15,0.24)', borderRadius: 14 },
  actionIconSecondary: { backgroundColor: palette.lime },
  authMenu: { height: 47, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 },
  authPrompt: { color: palette.muted, fontSize: 9 },
  authMenuItem: { minHeight: 34, paddingHorizontal: 7, flexDirection: 'row', alignItems: 'center', gap: 4 },
  authMenuText: { color: palette.forest, fontSize: 9, fontWeight: '900' },
  menuDivider: { width: 1, height: 14, backgroundColor: palette.line },
  finalActions: { gap: 9 },
});
