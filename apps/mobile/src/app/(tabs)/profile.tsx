import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useState } from 'react';
import { Alert, Pressable, StyleSheet, Switch, Text, TextInput, View } from 'react-native';
import { AppScreen, Avatar, Brand, Chip, GlassCard, PrimaryButton, ScreenHeader } from '@/components/ui';
import { palette, radii } from '@/constants/design';
import { useSession } from '@/context/SessionContext';
import { apiRequest, API_URL, User } from '@/lib/api';

const stylesList = [
  ['RELAXATION', 'Nghỉ dưỡng'],
  ['CULTURE', 'Văn hoá'],
  ['ADVENTURE', 'Phiêu lưu'],
  ['FOOD_TOUR', 'Ẩm thực'],
  ['FAMILY', 'Gia đình'],
  ['BUDGET', 'Tiết kiệm'],
] as const;

export default function ProfileScreen() {
  const { user, logout, updateLocalUser } = useSession();
  const [form, setForm] = useState(() => ({
    fullName: user?.fullName ?? '',
    bio: user?.bio ?? '',
    travelStyle: user?.travelStyle ?? 'CULTURE',
  }));
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [notifications, setNotifications] = useState(true);

  async function save() {
    setSaving(true);
    setMessage('');
    try {
      const updated = await apiRequest<User>('/api/v1/users/me', { method: 'PUT', body: JSON.stringify(form) });
      await updateLocalUser(updated);
      setMessage('Đã cập nhật hồ sơ của bạn.');
    } catch (cause) {
      setMessage(cause instanceof Error ? cause.message : 'Chưa thể lưu hồ sơ.');
    } finally {
      setSaving(false);
    }
  }

  function confirmLogout() {
    Alert.alert('Đăng xuất TravelMate?', 'Phiên trên thiết bị này sẽ được xoá an toàn.', [
      { text: 'Ở lại', style: 'cancel' },
      { text: 'Đăng xuất', style: 'destructive', onPress: async () => { await logout(); router.replace('/(auth)/welcome'); } },
    ]);
  }

  return (
    <AppScreen>
      <View style={styles.topbar}><Brand compact /><Pressable onPress={confirmLogout} style={styles.logoutIcon}><Ionicons name="log-out-outline" size={20} color={palette.danger} /></Pressable></View>
      <ScreenHeader eyebrow="KHÔNG GIAN CỦA BẠN" title="Hồ sơ cá nhân" subtitle="Điều chỉnh TravelMate theo cách bạn thích khám phá." />
      <GlassCard dark style={styles.identityCard}>
        <View style={styles.identityGlow} />
        <Avatar name={user?.fullName} size={68} light />
        <View style={styles.identityCopy}><Text style={styles.identityName}>{user?.fullName}</Text><Text style={styles.identityEmail}>{user?.email}</Text><View style={styles.identityBadges}><Chip label={user?.role ?? 'USER'} active /><Chip label={user?.emailVerified ? 'Đã xác thực' : 'Tài khoản local'} icon="checkmark-circle" /></View></View>
      </GlassCard>

      <GlassCard style={styles.formCard}>
        <View style={styles.cardHeading}><View style={styles.cardIcon}><Ionicons name="person-outline" size={18} color={palette.ink} /></View><View><Text style={styles.cardTitle}>Thông tin hiển thị</Text><Text style={styles.cardSubtitle}>Được dùng trong chuyến đi nhóm và AI chat.</Text></View></View>
        <Field label="Họ và tên" value={form.fullName} onChangeText={(fullName) => setForm({ ...form, fullName })} />
        <Field label="Giới thiệu ngắn" value={form.bio} onChangeText={(bio) => setForm({ ...form, bio })} placeholder="Bạn thích kiểu hành trình nào?" multiline style={styles.bioInput} />
        <View><Text style={styles.label}>Phong cách mặc định</Text><View style={styles.chips}>{stylesList.map(([value, label]) => <Chip key={value} label={label} active={form.travelStyle === value} onPress={() => setForm({ ...form, travelStyle: value })} />)}</View></View>
        {message ? <Text style={[styles.message, message.startsWith('Đã') && styles.success]}>{message}</Text> : null}
        <PrimaryButton label="Lưu thay đổi" icon="checkmark" loading={saving} onPress={save} />
      </GlassCard>

      <GlassCard style={styles.settingsCard}>
        <SettingRow icon="notifications-outline" title="Nhắc lịch hành trình" subtitle="Nhận thông báo trước hoạt động" action={<Switch value={notifications} onValueChange={setNotifications} trackColor={{ false: '#CDD6CF', true: palette.lime }} thumbColor={palette.white} />} />
        <View style={styles.divider} />
        <SettingRow icon="server-outline" title="Core API đang dùng" subtitle={API_URL} action={<View style={styles.onlineDot} />} />
        <View style={styles.divider} />
        <Pressable onPress={() => router.push('/profile/change-password')}><SettingRow icon="key-outline" title="Đổi mật khẩu" subtitle="Cập nhật bảo mật tài khoản" action={<Ionicons name="chevron-forward" size={17} color={palette.muted} />} /></Pressable>
        <View style={styles.divider} />
        <SettingRow icon="shield-checkmark-outline" title="Phiên đăng nhập" subtitle="Token được lưu bằng Secure Store" action={<Ionicons name="chevron-forward" size={17} color={palette.muted} />} />
      </GlassCard>

      <PrimaryButton label="Đăng xuất khỏi thiết bị" icon="log-out-outline" variant="ghost" onPress={confirmLogout} />
      <Text style={styles.version}>TRAVELMATE NATIVE • EXPO SDK 57 • VERSION 1.0</Text>
    </AppScreen>
  );
}

function Field({ label, style, ...props }: React.ComponentProps<typeof TextInput> & { label: string; style?: object }) {
  return <View><Text style={styles.label}>{label}</Text><TextInput style={[styles.input, style]} placeholderTextColor="#91A09A" {...props} /></View>;
}

function SettingRow({ icon, title, subtitle, action }: { icon: keyof typeof Ionicons.glyphMap; title: string; subtitle: string; action: React.ReactNode }) {
  return <View style={styles.settingRow}><View style={styles.settingIcon}><Ionicons name={icon} size={18} color={palette.forestLight} /></View><View style={styles.settingCopy}><Text style={styles.settingTitle}>{title}</Text><Text style={styles.settingSubtitle} numberOfLines={1}>{subtitle}</Text></View>{action}</View>;
}

const styles = StyleSheet.create({
  topbar: { minHeight: 50, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  logoutIcon: { width: 42, height: 42, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FFF0EC', borderRadius: 14 },
  identityCard: { minHeight: 132, flexDirection: 'row', alignItems: 'center', gap: 15, overflow: 'hidden' },
  identityGlow: { width: 180, height: 180, position: 'absolute', top: -100, right: -55, backgroundColor: 'rgba(201,244,90,0.20)', borderRadius: 90 },
  identityCopy: { flex: 1 },
  identityName: { color: palette.white, fontSize: 20, fontWeight: '900', letterSpacing: -0.7 },
  identityEmail: { marginTop: 4, color: 'rgba(255,255,255,0.52)', fontSize: 8 },
  identityBadges: { marginTop: 11, flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  formCard: { gap: 15 },
  cardHeading: { marginBottom: 2, flexDirection: 'row', alignItems: 'center', gap: 10 },
  cardIcon: { width: 42, height: 42, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 14 },
  cardTitle: { color: palette.ink, fontSize: 14, fontWeight: '900' },
  cardSubtitle: { marginTop: 3, color: palette.muted, fontSize: 7 },
  label: { marginBottom: 7, color: palette.inkSoft, fontSize: 8, fontWeight: '900' },
  input: { minHeight: 50, paddingHorizontal: 14, color: palette.ink, backgroundColor: '#F7F9F3', borderWidth: 1, borderColor: palette.line, borderRadius: radii.md, fontSize: 11, fontWeight: '700' },
  bioInput: { minHeight: 78, paddingTop: 13, textAlignVertical: 'top' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 },
  message: { padding: 10, color: palette.danger, backgroundColor: '#FFF0EC', borderRadius: radii.sm, fontSize: 8 },
  success: { color: '#3F785C', backgroundColor: '#E9F6ED' },
  settingsCard: { paddingVertical: 8 },
  settingRow: { minHeight: 68, flexDirection: 'row', alignItems: 'center', gap: 11 },
  settingIcon: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.sage, borderRadius: 14 },
  settingCopy: { flex: 1, minWidth: 0 },
  settingTitle: { color: palette.ink, fontSize: 10, fontWeight: '900' },
  settingSubtitle: { marginTop: 4, color: palette.muted, fontSize: 7 },
  divider: { height: 1, marginLeft: 51, backgroundColor: palette.line },
  onlineDot: { width: 10, height: 10, backgroundColor: '#59B57A', borderWidth: 3, borderColor: '#DFF3E6', borderRadius: 5 },
  version: { color: '#93A19C', textAlign: 'center', fontSize: 6, fontWeight: '800', letterSpacing: 1 },
});
