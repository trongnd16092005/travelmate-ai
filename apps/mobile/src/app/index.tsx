import { router } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function WelcomeScreen() {
  return (
    <View style={styles.container}>
      <SafeAreaView style={styles.content}>
        <View style={styles.hero}>
          <Text style={styles.eyebrow}>TRAVELMATE AI</Text>
          <Text style={styles.title}>Lập kế hoạch chuyến đi thông minh</Text>
          <Text style={styles.description}>
            Quản lý lịch trình, chi phí và nhận gợi ý phù hợp cho mỗi hành trình.
          </Text>
        </View>

        <Pressable style={styles.button} onPress={() => router.replace('/(tabs)')}>
          <Text style={styles.buttonText}>Bắt đầu</Text>
        </Pressable>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F4FAF7',
  },
  content: {
    flex: 1,
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingVertical: 32,
  },
  hero: {
    flex: 1,
    justifyContent: 'center',
    gap: 16,
  },
  eyebrow: {
    color: '#16775A',
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 1.5,
  },
  title: {
    color: '#17352D',
    fontSize: 44,
    fontWeight: '800',
    lineHeight: 48,
  },
  description: {
    color: '#557068',
    fontSize: 17,
    lineHeight: 26,
  },
  button: {
    alignItems: 'center',
    borderRadius: 16,
    backgroundColor: '#16775A',
    paddingVertical: 16,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
});
