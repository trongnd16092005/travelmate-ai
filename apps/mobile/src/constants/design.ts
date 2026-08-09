export const palette = {
  ink: '#10130F',
  inkSoft: '#232821',
  forest: '#286A40',
  forestLight: '#3D8E58',
  leaf: '#3E8B59',
  leafDark: '#23613B',
  lime: '#F2CE20',
  limeSoft: '#FFF1A0',
  cream: '#E5E6E2',
  paper: '#F7F7F4',
  sage: '#D6DED3',
  mint: '#C9DDCE',
  muted: '#6C726C',
  line: 'rgba(16, 19, 15, 0.10)',
  whiteLine: 'rgba(255,255,255,0.22)',
  coral: '#FF775D',
  amber: '#F3BA55',
  blue: '#61A8E8',
  white: '#FFFFFF',
  danger: '#B44332',
} as const;

export const radii = {
  sm: 12,
  md: 18,
  lg: 24,
  xl: 30,
  pill: 999,
} as const;

export const shadows = {
  card: {
    shadowColor: '#10130F',
    shadowOpacity: 0.08,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 9 },
    elevation: 4,
  },
  dark: {
    shadowColor: '#031D17',
    shadowOpacity: 0.24,
    shadowRadius: 26,
    shadowOffset: { width: 0, height: 14 },
    elevation: 8,
  },
} as const;

export const tripImages = {
  hue: require('../../assets/images/hue-citadel-online.jpg'),
  heritage: require('../../assets/images/travelmate-hero.png'),
  coast: require('../../assets/images/phu-yen-coast.jpg'),
  mountain: require('../../assets/images/ha-giang-pass.jpg'),
};

/**
 * Local artwork is only used when it actually matches the destination.
 * Unknown destinations intentionally return no local image: the media hook
 * will resolve a real page image instead of briefly showing Huế everywhere.
 */
export function fallbackImageForDestination(destination?: string) {
  const normalized = (destination ?? '').toLocaleLowerCase('vi');
  if (normalized.includes('hà giang') || normalized.includes('sapa')) return tripImages.mountain;
  if (normalized.includes('phú yên') || normalized.includes('nha trang') || normalized.includes('đà nẵng')) return tripImages.coast;
  if (normalized.includes('hội an')) return tripImages.heritage;
  if (normalized.includes('huế') || normalized.includes('thừa thiên')) return tripImages.hue;
  return null;
}

/** @deprecated Prefer useDestinationImage so arbitrary cities resolve online. */
export function imageForDestination(destination?: string) {
  return fallbackImageForDestination(destination) ?? { uri: '' };
}
