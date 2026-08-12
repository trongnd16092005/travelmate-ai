import { Ionicons } from '@expo/vector-icons';
import { useEffect, useRef } from 'react';
import { Animated, StyleSheet, View } from 'react-native';

import { palette } from '@/constants/design';

type IconName = keyof typeof Ionicons.glyphMap;

type AnimatedTabIconProps = {
  focused: boolean;
  icon: IconName;
  color: string;
};

export function AnimatedTabIcon({ focused, icon, color }: AnimatedTabIconProps) {
  const progress = useRef(new Animated.Value(focused ? 1 : 0)).current;
  const filled = icon.replace('-outline', '') as IconName;

  useEffect(() => {
    Animated.spring(progress, {
      toValue: focused ? 1 : 0,
      damping: 13,
      stiffness: 210,
      mass: 0.65,
      useNativeDriver: true,
    }).start();
  }, [focused, progress]);

  const iconMotion = {
    transform: [
      { translateY: progress.interpolate({ inputRange: [0, 1], outputRange: [0, -1] }) },
      { scale: progress.interpolate({ inputRange: [0, 1], outputRange: [1, 1.12] }) },
    ],
  };

  const haloMotion = {
    opacity: progress.interpolate({ inputRange: [0, 1], outputRange: [0, 0.32] }),
    transform: [{ scale: progress.interpolate({ inputRange: [0, 1], outputRange: [0.72, 1.15] }) }],
  };

  return (
    <View style={styles.slot}>
      <Animated.View style={[styles.halo, haloMotion]} />
      <Animated.View style={[styles.iconSurface, focused && styles.iconSurfaceActive, iconMotion]}>
        <Ionicons
          name={focused ? filled : icon}
          color={focused ? palette.ink : color}
          size={focused ? 21 : 20}
        />
      </Animated.View>
      <Animated.View style={[styles.activeDot, { opacity: progress }]} />
    </View>
  );
}

const styles = StyleSheet.create({
  slot: {
    width: 44,
    height: 38,
    alignItems: 'center',
    justifyContent: 'center',
  },
  halo: {
    position: 'absolute',
    width: 38,
    height: 32,
    borderRadius: 15,
    backgroundColor: palette.lime,
  },
  iconSurface: {
    width: 35,
    height: 31,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconSurfaceActive: {
    backgroundColor: palette.lime,
    shadowColor: palette.lime,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.38,
    shadowRadius: 9,
    elevation: 7,
  },
  activeDot: {
    position: 'absolute',
    bottom: -1,
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: palette.lime,
  },
});
