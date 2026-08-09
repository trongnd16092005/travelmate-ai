import { Ionicons } from '@expo/vector-icons';
import { Redirect, Tabs } from 'expo-router';
import { Platform } from 'react-native';
import { useSession } from '@/context/SessionContext';
import { palette, shadows } from '@/constants/design';
import { AnimatedTabIcon } from '@/components/navigation/AnimatedTabIcon';

const icons: Record<string, keyof typeof Ionicons.glyphMap> = {
  home: 'home-outline',
  trips: 'map-outline',
  map: 'navigate-outline',
  ai: 'sparkles-outline',
  profile: 'person-outline',
};

export default function TabsLayout() {
  const { booting, signedIn } = useSession();
  if (!booting && !signedIn) return <Redirect href="/(auth)/welcome" />;
  return (
    <Tabs
      initialRouteName="home"
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarHideOnKeyboard: true,
        tabBarShowLabel: true,
        animation: 'fade',
        transitionSpec: {
          animation: 'timing',
          config: { duration: 170 },
        },
        tabBarActiveTintColor: palette.lime,
        tabBarInactiveTintColor: 'rgba(255,255,255,0.48)',
        tabBarLabelStyle: {
          fontSize: 8,
          lineHeight: 10,
          fontWeight: '800',
          letterSpacing: 0.05,
          marginTop: 0,
        },
        tabBarIconStyle: { marginTop: 1 },
        tabBarItemStyle: { paddingTop: 3 },
        tabBarIcon: ({ color, size, focused }) => {
          const outline = icons[route.name] ?? 'ellipse-outline';
          return <AnimatedTabIcon focused={focused} icon={outline} color={color} />;
        },
        tabBarStyle: {
          position: 'absolute',
          left: 10,
          right: 10,
          bottom: Platform.OS === 'ios' ? 0 : 3,
          height: Platform.OS === 'ios' ? 79 : 70,
          paddingTop: 4,
          paddingBottom: Platform.OS === 'ios' ? 13 : 6,
          backgroundColor: '#0B0D0B',
          borderTopWidth: 0,
          borderWidth: 1,
          borderColor: 'rgba(255,255,255,0.07)',
          borderRadius: 26,
          ...shadows.dark,
        },
      })}
    >
      <Tabs.Screen name="home" options={{ title: 'Trang chủ' }} />
      <Tabs.Screen name="trips" options={{ title: 'Chuyến đi' }} />
      <Tabs.Screen name="map" options={{ title: 'Bản đồ' }} />
      <Tabs.Screen name="ai" options={{ title: 'TravelMate AI' }} />
      <Tabs.Screen name="profile" options={{ title: 'Hồ sơ' }} />
    </Tabs>
  );
}
