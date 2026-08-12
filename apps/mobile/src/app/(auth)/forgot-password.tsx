import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Brand, PrimaryButton } from '@/components/ui';
import { palette, radii } from '@/constants/design';
import { apiRequest } from '@/lib/api';

export default function ForgotPasswordScreen() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  async function send() {
    if (!email.includes('@')) { setError('Nhập email hợp lệ.'); return; }
    setLoading(true); setError('');
    try {
      await apiRequest('/api/v1/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) });
      router.push({ pathname: '/(auth)/reset-password', params: { email } });
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Chưa thể gửi mã xác nhận.'); }
    finally { setLoading(false); }
  }
  return <SafeAreaView style={styles.screen}><View style={styles.top}><Pressable onPress={() => router.back()} style={styles.back}><Ionicons name="arrow-back" size={20} /></Pressable><Brand compact /></View><View style={styles.content}><View style={styles.icon}><Ionicons name="key-outline" size={28} color={palette.ink} /></View><Text style={styles.eyebrow}>KHÔI PHỤC TÀI KHOẢN</Text><Text style={styles.title}>Quên mật khẩu?</Text><Text style={styles.subtitle}>Nhập email đã đăng ký. TravelMate sẽ gửi mã xác nhận để bạn đặt mật khẩu mới.</Text><Text style={styles.label}>Email</Text><TextInput value={email} onChangeText={setEmail} placeholder="ban@example.com" placeholderTextColor="#91A09A" keyboardType="email-address" autoCapitalize="none" style={styles.input} />{error ? <Text style={styles.error}>{error}</Text> : null}<PrimaryButton label="Gửi mã xác nhận" loading={loading} onPress={send} /></View></SafeAreaView>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, padding: 20, backgroundColor: palette.cream },
  top: { minHeight: 50, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  back: { width: 42, height: 42, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.white, borderRadius: 14 },
  content: { flex: 1, justifyContent: 'center' },
  icon: { width: 58, height: 58, marginBottom: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.lime, borderRadius: 20 },
  eyebrow: { color: '#75921F', fontSize: 8, fontWeight: '900', letterSpacing: 1.2 },
  title: { marginTop: 10, color: palette.ink, fontSize: 39, fontWeight: '900', letterSpacing: -2 },
  subtitle: { marginTop: 12, marginBottom: 28, color: palette.muted, fontSize: 11, lineHeight: 18 },
  label: { marginBottom: 7, color: palette.ink, fontSize: 8, fontWeight: '900' },
  input: { height: 54, marginBottom: 13, paddingHorizontal: 14, color: palette.ink, backgroundColor: palette.white, borderWidth: 1, borderColor: palette.line, borderRadius: radii.md, fontSize: 11, fontWeight: '700' },
  error: { marginBottom: 12, padding: 10, color: palette.danger, backgroundColor: '#FFF0EC', borderRadius: 12, fontSize: 8 },
});
