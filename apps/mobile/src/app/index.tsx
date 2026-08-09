import { Redirect } from 'expo-router';
import { View } from 'react-native';
import { LoadingState } from '@/components/ui';
import { palette } from '@/constants/design';
import { useSession } from '@/context/SessionContext';

export default function Index() {
  const { booting, signedIn } = useSession();
  if (booting) return <View style={{ flex: 1, backgroundColor: palette.cream, justifyContent: 'center' }}><LoadingState /></View>;
  return <Redirect href={signedIn ? '/(tabs)/home' : '/(auth)/welcome'} />;
}
