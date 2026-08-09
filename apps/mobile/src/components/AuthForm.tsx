import { Ionicons } from '@expo/vector-icons';
import { Href, router, useLocalSearchParams } from 'expo-router';
import { ComponentProps, useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Brand, PrimaryButton } from '@/components/ui';
import { palette, radii, shadows } from '@/constants/design';
import { useSession } from '@/context/SessionContext';

export function AuthForm({ mode }: { mode: 'login' | 'register' }) {
  const isRegister = mode === 'register';
  const { login, register } = useSession();
  const { next: nextParam } = useLocalSearchParams<{ next?: string | string[] }>();
  const nextRoute = getSafeNextRoute(nextParam);
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function submit() {
    setError('');
    if (!email.includes('@') || password.length < 8 || (isRegister && fullName.trim().length < 2)) {
      setError('Vui lòng nhập đủ thông tin; mật khẩu cần ít nhất 8 ký tự.');
      return;
    }
    if (isRegister && !/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/.test(password)) {
      setError('Mật khẩu cần có chữ hoa, chữ thường và ít nhất một chữ số.');
      return;
    }
    setLoading(true);
    try {
      if (isRegister) await register(fullName, email, password);
      else await login(email, password);
      router.replace((nextRoute ?? '/(tabs)/home') as Href);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không thể đăng nhập lúc này.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView style={styles.screen} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <SafeAreaView style={styles.safe}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
          <View style={styles.topbar}>
            <Pressable onPress={() => router.back()} style={styles.back}><Ionicons name="arrow-back" size={20} color={palette.ink} /></Pressable>
            <Brand compact />
          </View>
          <View style={styles.heading}>
            <Text style={styles.eyebrow}>{isRegister ? 'BẮT ĐẦU MIỄN PHÍ' : 'CHÀO MỪNG TRỞ LẠI'}</Text>
            <Text style={styles.title}>{isRegister ? 'Tạo hành trình đầu tiên.' : 'Tiếp tục chuyến đi.'}</Text>
            <Text style={styles.subtitle}>{isRegister ? 'Một tài khoản cho lịch trình, bản đồ, ngân sách và TravelMate AI.' : 'Mọi kế hoạch của bạn vẫn đang được giữ nguyên.'}</Text>
          </View>
          <View style={styles.form}>
            {isRegister && <Field icon="person-outline" placeholder="Họ và tên" value={fullName} onChangeText={setFullName} autoCapitalize="words" />}
            <Field icon="mail-outline" placeholder="Email" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" />
            <View style={styles.field}>
              <Ionicons name="lock-closed-outline" size={18} color={palette.muted} />
              <TextInput style={styles.input} placeholder="Mật khẩu" placeholderTextColor="#91A09A" value={password} onChangeText={setPassword} secureTextEntry={!showPassword} autoCapitalize="none" />
              <Pressable onPress={() => setShowPassword((value) => !value)}><Ionicons name={showPassword ? 'eye-off-outline' : 'eye-outline'} size={19} color={palette.muted} /></Pressable>
            </View>
            {!isRegister && <Pressable onPress={() => router.push('/(auth)/forgot-password')} style={styles.forgot}><Text style={styles.forgotText}>Quên mật khẩu?</Text><Ionicons name="arrow-forward" size={13} color="#668314" /></Pressable>}
            {error ? <View style={styles.error}><Ionicons name="alert-circle-outline" size={16} color={palette.danger} /><Text style={styles.errorText}>{error}</Text></View> : null}
            <PrimaryButton label={isRegister ? 'Tạo tài khoản' : 'Đăng nhập'} icon={isRegister ? 'sparkles' : 'arrow-forward'} loading={loading} onPress={submit} />
          </View>
          <Pressable
            onPress={() => {
              const pathname = isRegister ? '/(auth)/login' : '/(auth)/register';
              if (nextRoute) router.replace({ pathname, params: { next: nextRoute } });
              else router.replace(pathname);
            }}
            style={styles.switch}
          >
            <Text style={styles.switchText}>{isRegister ? 'Đã có tài khoản? ' : 'Chưa có tài khoản? '}<Text style={styles.switchStrong}>{isRegister ? 'Đăng nhập' : 'Đăng ký miễn phí'}</Text></Text>
          </Pressable>
          <View style={styles.benefits}>
            {['Lưu phiên an toàn', 'AI hiểu chuyến đi', 'Đồng bộ với web'].map((item) => <View key={item} style={styles.benefit}><Ionicons name="checkmark-circle" size={15} color="#76951E" /><Text style={styles.benefitText}>{item}</Text></View>)}
          </View>
        </ScrollView>
      </SafeAreaView>
    </KeyboardAvoidingView>
  );
}

function getSafeNextRoute(value?: string | string[]) {
  const route = Array.isArray(value) ? value[0] : value;
  if (!route) return null;
  return /^\/invitations\/accept\?token=[A-Za-z0-9._~-]+$/.test(route) ? route : null;
}

function Field(props: ComponentProps<typeof TextInput> & { icon: keyof typeof Ionicons.glyphMap }) {
  const { icon, ...inputProps } = props;
  return <View style={styles.field}><Ionicons name={icon} size={18} color={palette.muted} /><TextInput style={styles.input} placeholderTextColor="#91A09A" {...inputProps} /></View>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.cream },
  safe: { flex: 1 },
  content: { minHeight: '100%', padding: 20, paddingBottom: 42 },
  topbar: { minHeight: 52, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  back: { width: 42, height: 42, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.72)', borderWidth: 1, borderColor: palette.line, borderRadius: 15 },
  heading: { marginTop: 52, marginBottom: 30 },
  eyebrow: { color: '#76931F', fontSize: 8, fontWeight: '900', letterSpacing: 1.3 },
  title: { maxWidth: 330, marginTop: 12, color: palette.ink, fontSize: 39, lineHeight: 41, fontWeight: '900', letterSpacing: -2 },
  subtitle: { maxWidth: 330, marginTop: 12, color: palette.muted, fontSize: 11, lineHeight: 18 },
  form: { gap: 13 },
  field: { height: 56, paddingHorizontal: 15, flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: 'rgba(255,255,252,0.86)', borderWidth: 1, borderColor: 'rgba(12,51,41,0.10)', borderRadius: radii.md, ...shadows.card },
  input: { flex: 1, color: palette.ink, fontSize: 12, fontWeight: '700' },
  error: { padding: 12, flexDirection: 'row', alignItems: 'flex-start', gap: 8, backgroundColor: '#FFF0EC', borderRadius: radii.sm },
  errorText: { flex: 1, color: palette.danger, fontSize: 10, lineHeight: 16 },
  forgot: { alignSelf: 'flex-end', paddingVertical: 3, flexDirection: 'row', alignItems: 'center', gap: 5 },
  forgotText: { color: '#668314', fontSize: 9, fontWeight: '900' },
  switch: { minHeight: 54, alignItems: 'center', justifyContent: 'center' },
  switchText: { color: palette.muted, fontSize: 10 },
  switchStrong: { color: '#668314', fontWeight: '900' },
  benefits: { marginTop: 42, flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', gap: 8 },
  benefit: { paddingHorizontal: 10, paddingVertical: 8, flexDirection: 'row', alignItems: 'center', gap: 5, backgroundColor: 'rgba(255,255,255,0.56)', borderRadius: radii.pill },
  benefitText: { color: palette.muted, fontSize: 8 },
});
