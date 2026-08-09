import { Ionicons } from '@expo/vector-icons';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Brand, PrimaryButton } from '@/components/ui';
import { palette, radii } from '@/constants/design';
import { apiRequest } from '@/lib/api';

export default function ResetPasswordScreen() {
  const params = useLocalSearchParams<{ email?: string }>();
  const [email, setEmail] = useState(params.email ?? '');
  const [otp, setOtp] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  async function reset() {
    if (!email.includes('@') || otp.length !== 6 || password.length < 8) { setError('Kiểm tra email, mã OTP 6 số và mật khẩu tối thiểu 8 ký tự.'); return; }
    if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/.test(password)) { setError('Mật khẩu cần có chữ hoa, chữ thường và ít nhất một chữ số.'); return; }
    setLoading(true); setError('');
    try {
      await apiRequest('/api/v1/auth/reset-password', { method: 'POST', body: JSON.stringify({ email, otp, newPassword: password }) });
      router.replace('/(auth)/login');
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Chưa thể đổi mật khẩu.'); }
    finally { setLoading(false); }
  }
  return <SafeAreaView style={styles.screen}><View style={styles.top}><Pressable onPress={() => router.back()} style={styles.back}><Ionicons name="arrow-back" size={20} /></Pressable><Brand compact /></View><View style={styles.content}><Text style={styles.eyebrow}>XÁC NHẬN DANH TÍNH</Text><Text style={styles.title}>Đặt mật khẩu mới.</Text><Text style={styles.subtitle}>Nhập mã xác nhận trong email và mật khẩu mới cho TravelMate.</Text><Field label="Email" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" /><Field label="Mã OTP" value={otp} onChangeText={setOtp} keyboardType="number-pad" /><Field label="Mật khẩu mới" value={password} onChangeText={setPassword} secureTextEntry />{error ? <Text style={styles.error}>{error}</Text> : null}<PrimaryButton label="Cập nhật mật khẩu" loading={loading} onPress={reset} /></View></SafeAreaView>;
}

function Field({ label, ...props }: React.ComponentProps<typeof TextInput> & { label: string }) { return <View style={styles.field}><Text style={styles.label}>{label}</Text><TextInput style={styles.input} placeholderTextColor="#91A09A" {...props} /></View>; }
const styles = StyleSheet.create({
  screen: { flex: 1, padding: 20, backgroundColor: palette.cream },
  top: { minHeight: 50, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  back: { width: 42, height: 42, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.white, borderRadius: 14 },
  content: { flex: 1, justifyContent: 'center' },
  eyebrow: { color: '#75921F', fontSize: 8, fontWeight: '900', letterSpacing: 1.2 },
  title: { maxWidth: 310, marginTop: 10, color: palette.ink, fontSize: 39, lineHeight: 42, fontWeight: '900', letterSpacing: -2 },
  subtitle: { marginTop: 12, marginBottom: 24, color: palette.muted, fontSize: 11, lineHeight: 18 },
  field: { marginBottom: 12 },
  label: { marginBottom: 7, color: palette.ink, fontSize: 8, fontWeight: '900' },
  input: { height: 52, paddingHorizontal: 14, color: palette.ink, backgroundColor: palette.white, borderWidth: 1, borderColor: palette.line, borderRadius: radii.md, fontSize: 11, fontWeight: '700' },
  error: { marginBottom: 12, padding: 10, color: palette.danger, backgroundColor: '#FFF0EC', borderRadius: 12, fontSize: 8 },
});
