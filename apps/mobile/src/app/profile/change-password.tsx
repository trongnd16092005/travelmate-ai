import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Brand, PrimaryButton } from '@/components/ui';
import { palette, radii } from '@/constants/design';
import { apiRequest } from '@/lib/api';

export default function ChangePasswordScreen() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  async function save() {
    if (newPassword.length < 8 || newPassword !== confirm) { setMessage('Mật khẩu mới cần ít nhất 8 ký tự và phải khớp nhau.'); return; }
    setLoading(true); setMessage('');
    try {
      await apiRequest('/api/v1/users/me/password', { method: 'PUT', body: JSON.stringify({ currentPassword, newPassword }) });
      setMessage('Đã đổi mật khẩu thành công.');
      setTimeout(() => router.back(), 700);
    } catch (cause) { setMessage(cause instanceof Error ? cause.message : 'Chưa thể đổi mật khẩu.'); }
    finally { setLoading(false); }
  }
  return <SafeAreaView style={styles.screen}><View style={styles.top}><Pressable onPress={() => router.back()} style={styles.back}><Ionicons name="arrow-back" size={20} /></Pressable><Brand compact /></View><View style={styles.content}><View style={styles.icon}><Ionicons name="shield-checkmark-outline" size={28} color={palette.ink} /></View><Text style={styles.eyebrow}>BẢO MẬT TÀI KHOẢN</Text><Text style={styles.title}>Đổi mật khẩu.</Text><Text style={styles.subtitle}>Mật khẩu mạnh giúp bảo vệ lịch trình và dữ liệu chuyến đi của bạn.</Text><Field label="Mật khẩu hiện tại" value={currentPassword} onChangeText={setCurrentPassword} secureTextEntry /><Field label="Mật khẩu mới" value={newPassword} onChangeText={setNewPassword} secureTextEntry /><Field label="Nhập lại mật khẩu" value={confirm} onChangeText={setConfirm} secureTextEntry />{message ? <Text style={[styles.message, message.startsWith('Đã') && styles.success]}>{message}</Text> : null}<PrimaryButton label="Cập nhật mật khẩu" icon="checkmark" loading={loading} onPress={save} /></View></SafeAreaView>;
}
function Field({ label, ...props }: React.ComponentProps<typeof TextInput> & { label: string }) { return <View style={styles.field}><Text style={styles.label}>{label}</Text><TextInput style={styles.input} placeholderTextColor="#91A09A" {...props} /></View>; }
const styles = StyleSheet.create({
  screen: { flex: 1, padding: 20, backgroundColor: palette.cream },
  top: { minHeight: 50, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  back: { width: 42, height: 42, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.white, borderRadius: 14 },
  content: { flex: 1, justifyContent: 'center' },
  icon: { width: 58, height: 58, marginBottom: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 20 },
  eyebrow: { color: '#75921F', fontSize: 8, fontWeight: '900', letterSpacing: 1.2 },
  title: { marginTop: 10, color: palette.ink, fontSize: 39, fontWeight: '900', letterSpacing: -2 },
  subtitle: { marginTop: 12, marginBottom: 24, color: palette.muted, fontSize: 11, lineHeight: 18 },
  field: { marginBottom: 12 },
  label: { marginBottom: 7, color: palette.ink, fontSize: 8, fontWeight: '900' },
  input: { height: 52, paddingHorizontal: 14, color: palette.ink, backgroundColor: palette.white, borderWidth: 1, borderColor: palette.line, borderRadius: radii.md, fontSize: 11, fontWeight: '700' },
  message: { marginBottom: 12, padding: 10, color: palette.danger, backgroundColor: '#FFF0EC', borderRadius: 12, fontSize: 8 },
  success: { color: '#3F785D', backgroundColor: '#E9F6ED' },
});
