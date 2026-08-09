import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { PropsWithChildren, ReactNode } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleProp,
  StyleSheet,
  Text,
  View,
  ViewStyle,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { palette, radii, shadows } from '@/constants/design';

export function AppScreen({ children, scroll = true, style }: PropsWithChildren<{ scroll?: boolean; style?: StyleProp<ViewStyle> }>) {
  const content = scroll ? (
    <ScrollView contentContainerStyle={[styles.screenContent, style]} showsVerticalScrollIndicator={false}>{children}</ScrollView>
  ) : (
    <View style={[styles.screenContent, styles.flex, style]}>{children}</View>
  );
  return (
    <View style={styles.screen}>
      <View style={[styles.glow, styles.glowOne]} />
      <View style={[styles.glow, styles.glowTwo]} />
      <SafeAreaView style={styles.flex} edges={['top']}>{content}</SafeAreaView>
    </View>
  );
}

export function Brand({ light = false, compact = false }: { light?: boolean; compact?: boolean }) {
  return (
    <View style={styles.brand}>
      <LinearGradient colors={[palette.forestLight, palette.forest]} style={[styles.brandMark, compact && styles.brandMarkCompact]}>
        <Ionicons name="airplane" size={compact ? 15 : 18} color={palette.white} />
      </LinearGradient>
      <View>
        <Text style={[styles.brandName, light && styles.textWhite, compact && styles.brandNameCompact]}>TravelMate<Text style={styles.brandDot}>.</Text></Text>
        {!compact && <Text style={[styles.brandTagline, light && styles.textWhiteMuted]}>AI TRAVEL COMPANION</Text>}
      </View>
    </View>
  );
}

export function GlassCard({ children, dark = false, style }: PropsWithChildren<{ dark?: boolean; style?: StyleProp<ViewStyle> }>) {
  return <View style={[styles.card, dark && styles.cardDark, style]}>{children}</View>;
}

export function PrimaryButton({ label, onPress, icon = 'arrow-forward', loading = false, variant = 'lime', disabled = false }: {
  label: string;
  onPress: () => void;
  icon?: keyof typeof Ionicons.glyphMap;
  loading?: boolean;
  variant?: 'lime' | 'dark' | 'ghost';
  disabled?: boolean;
}) {
  const colors: [string, string] = variant === 'dark' ? [palette.inkSoft, palette.ink] : variant === 'ghost' ? [palette.white, palette.white] : [palette.forestLight, palette.forest];
  return (
    <Pressable disabled={disabled || loading} onPress={onPress} style={({ pressed }) => [styles.buttonWrap, pressed && styles.pressed, (disabled || loading) && styles.disabled]}>
      <LinearGradient colors={colors} style={[styles.button, variant === 'ghost' && styles.buttonGhost]}>
        {loading ? <ActivityIndicator color={variant === 'ghost' ? palette.ink : palette.white} /> : <>
          <Text style={[styles.buttonLabel, variant !== 'ghost' && styles.textWhite]}>{label}</Text>
          <Ionicons name={icon} size={17} color={variant === 'ghost' ? palette.ink : palette.white} />
        </>}
      </LinearGradient>
    </Pressable>
  );
}

export function ScreenHeader({ eyebrow, title, subtitle, action }: { eyebrow?: string; title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <View style={styles.header}>
      <View style={styles.headerCopy}>
        {eyebrow && <Text style={styles.eyebrow}>{eyebrow}</Text>}
        <Text style={styles.headerTitle}>{title}</Text>
        {subtitle && <Text style={styles.headerSubtitle}>{subtitle}</Text>}
      </View>
      {action}
    </View>
  );
}

export function Chip({ label, icon, active = false, onPress }: { label: string; icon?: keyof typeof Ionicons.glyphMap; active?: boolean; onPress?: () => void }) {
  const content = <>{icon && <Ionicons name={icon} size={13} color={active ? palette.ink : palette.muted} />}<Text style={[styles.chipText, active && styles.chipTextActive]}>{label}</Text></>;
  if (onPress) return <Pressable onPress={onPress} style={[styles.chip, active && styles.chipActive]}>{content}</Pressable>;
  return <View style={[styles.chip, active && styles.chipActive]}>{content}</View>;
}

export function EmptyState({ icon = 'map-outline', title, message, action }: { icon?: keyof typeof Ionicons.glyphMap; title: string; message: string; action?: ReactNode }) {
  return (
    <GlassCard style={styles.emptyState}>
      <View style={styles.emptyIcon}><Ionicons name={icon} size={28} color={palette.forestLight} /></View>
      <Text style={styles.emptyTitle}>{title}</Text>
      <Text style={styles.emptyMessage}>{message}</Text>
      {action}
    </GlassCard>
  );
}

export function LoadingState({ label = 'Đang chuẩn bị hành trình...' }: { label?: string }) {
  return <View style={styles.loading}><ActivityIndicator color={palette.forestLight} /><Text style={styles.loadingText}>{label}</Text></View>;
}

export function Avatar({ name, size = 42, light = false }: { name?: string; size?: number; light?: boolean }) {
  const value = (name ?? 'TM').split(/\s+/).slice(-2).map((part) => part[0]?.toUpperCase()).join('');
  return <LinearGradient colors={light ? ['#FFFFFF', '#E9F4E4'] : [palette.limeSoft, palette.lime]} style={[styles.avatar, { width: size, height: size, borderRadius: size / 2 }]}><Text style={styles.avatarText}>{value}</Text></LinearGradient>;
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  screen: { flex: 1, backgroundColor: palette.cream, overflow: 'hidden' },
  screenContent: { paddingHorizontal: 18, paddingTop: 12, paddingBottom: 128, gap: 18 },
  glow: { position: 'absolute', borderRadius: 999, opacity: 0.14 },
  glowOne: { width: 220, height: 220, top: -120, right: -110, backgroundColor: palette.lime },
  glowTwo: { width: 230, height: 230, bottom: 10, left: -170, backgroundColor: palette.forestLight },
  brand: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  brandMark: { width: 42, height: 42, alignItems: 'center', justifyContent: 'center', borderRadius: 14, ...shadows.card },
  brandMarkCompact: { width: 34, height: 34, borderRadius: 11 },
  brandName: { color: palette.ink, fontSize: 19, lineHeight: 21, fontWeight: '900', letterSpacing: -0.8 },
  brandNameCompact: { fontSize: 16 },
  brandDot: { color: palette.forestLight },
  brandTagline: { marginTop: 2, color: palette.muted, fontSize: 6, fontWeight: '900', letterSpacing: 1.15 },
  textWhite: { color: palette.white },
  textWhiteMuted: { color: 'rgba(255,255,255,0.55)' },
  card: { padding: 18, backgroundColor: 'rgba(247,247,244,0.96)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.78)', borderRadius: radii.lg, ...shadows.card },
  cardDark: { backgroundColor: palette.ink, borderColor: palette.whiteLine, ...shadows.dark },
  buttonWrap: { alignSelf: 'stretch', borderRadius: radii.pill },
  button: { minHeight: 52, paddingHorizontal: 20, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9, borderRadius: radii.pill, ...shadows.card },
  buttonGhost: { borderWidth: 1, borderColor: palette.line, shadowOpacity: 0 },
  buttonLabel: { color: palette.ink, fontSize: 13, fontWeight: '900' },
  pressed: { transform: [{ scale: 0.98 }], opacity: 0.92 },
  disabled: { opacity: 0.55 },
  header: { minHeight: 70, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12 },
  headerCopy: { flex: 1 },
  eyebrow: { marginBottom: 5, color: palette.forest, fontSize: 8, fontWeight: '900', letterSpacing: 1.25 },
  headerTitle: { color: palette.ink, fontSize: 30, lineHeight: 34, fontWeight: '900', letterSpacing: -1.45 },
  headerSubtitle: { marginTop: 5, color: palette.muted, fontSize: 11, lineHeight: 17 },
  chip: { minHeight: 34, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, backgroundColor: 'rgba(255,255,255,0.66)', borderWidth: 1, borderColor: palette.line, borderRadius: radii.pill },
  chipActive: { backgroundColor: palette.lime, borderColor: 'rgba(16,19,15,0.08)' },
  chipText: { color: palette.muted, fontSize: 9, fontWeight: '800' },
  chipTextActive: { color: palette.ink },
  emptyState: { minHeight: 250, alignItems: 'center', justifyContent: 'center' },
  emptyIcon: { width: 58, height: 58, marginBottom: 15, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.sage, borderRadius: 20 },
  emptyTitle: { color: palette.ink, fontSize: 18, fontWeight: '900' },
  emptyMessage: { maxWidth: 270, marginTop: 7, marginBottom: 18, color: palette.muted, textAlign: 'center', fontSize: 11, lineHeight: 18 },
  loading: { minHeight: 220, alignItems: 'center', justifyContent: 'center', gap: 12 },
  loadingText: { color: palette.muted, fontSize: 11, fontWeight: '700' },
  avatar: { alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: 'rgba(255,255,255,0.7)' },
  avatarText: { color: palette.ink, fontSize: 11, fontWeight: '900' },
});
