import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function HomeScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <View>
        <Text style={styles.eyebrow}>TRAVELMATE AI</Text>
        <Text style={styles.title}>Hành trình của bạn</Text>
        <Text style={styles.description}>Tạo chuyến đi mới và để AI hỗ trợ lên lịch trình.</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 24,
    backgroundColor: '#F4FAF7',
  },
  eyebrow: {
    color: '#16775A',
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 1.2,
  },
  title: {
    marginTop: 12,
    color: '#17352D',
    fontSize: 32,
    fontWeight: '800',
  },
  description: {
    marginTop: 12,
    color: '#557068',
    fontSize: 16,
    lineHeight: 24,
  },
});
