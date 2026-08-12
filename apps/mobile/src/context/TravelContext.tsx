import { createContext, PropsWithChildren, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { apiRequest, Trip } from '@/lib/api';
import { useSession } from '@/context/SessionContext';

type TravelContextValue = {
  trips: Trip[];
  activeTrip: Trip | null;
  activeTripId: number | null;
  loadingTrips: boolean;
  setActiveTripId: (id: number | null) => void;
  reloadTrips: () => Promise<void>;
};

const TravelContext = createContext<TravelContextValue | null>(null);

export function TravelProvider({ children }: PropsWithChildren) {
  const { signedIn } = useSession();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [activeTripId, setActiveTripId] = useState<number | null>(null);
  const [loadingTrips, setLoadingTrips] = useState(false);

  const reloadTrips = useCallback(async () => {
    if (!signedIn) {
      setTrips([]);
      setActiveTripId(null);
      return;
    }
    setLoadingTrips(true);
    try {
      const page = await apiRequest<{ items: Trip[] }>('/api/v1/trips?size=50');
      setTrips(page.items);
      setActiveTripId((current) => current && page.items.some((trip) => trip.id === current) ? current : page.items[0]?.id ?? null);
    } finally {
      setLoadingTrips(false);
    }
  }, [signedIn]);

  useEffect(() => {
    reloadTrips().catch(() => undefined);
  }, [reloadTrips]);

  const activeTrip = trips.find((trip) => trip.id === activeTripId) ?? null;
  const value = useMemo(() => ({ trips, activeTrip, activeTripId, loadingTrips, setActiveTripId, reloadTrips }), [trips, activeTrip, activeTripId, loadingTrips, reloadTrips]);

  return <TravelContext.Provider value={value}>{children}</TravelContext.Provider>;
}

export function useTravel() {
  const value = useContext(TravelContext);
  if (!value) throw new Error('useTravel must be used inside TravelProvider');
  return value;
}
