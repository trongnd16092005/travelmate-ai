import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function LoginScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <View>
        <Text style={styles.title}>Đăng nhập</Text>
        <Text style={styles.description}>Màn hình xác thực sẽ được phát triển tại đây.</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
    backgroundColor: '#F4FAF7',
  },
  title: {
    color: '#17352D',
    fontSize: 32,
    fontWeight: '800',
  },
  description: {
    marginTop: 12,
    color: '#557068',
    fontSize: 16,
  },
});
