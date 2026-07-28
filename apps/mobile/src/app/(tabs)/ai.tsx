import { StyleSheet, Text, View } from 'react-native';

export default function AiScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Trợ lý AI</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F4FAF7',
  },
  title: {
    color: '#17352D',
    fontSize: 28,
    fontWeight: '800',
  },
});
