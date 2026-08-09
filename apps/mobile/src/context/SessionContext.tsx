import { createContext, PropsWithChildren, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { apiRequest, authApi, getStoredUser, hasSession, setStoredUser, User } from '@/lib/api';

type SessionContextValue = {
  booting: boolean;
  signedIn: boolean;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  register: (fullName: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  updateLocalUser: (user: User) => Promise<void>;
};

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: PropsWithChildren) {
  const [booting, setBooting] = useState(true);
  const [signedIn, setSignedIn] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    Promise.all([hasSession(), getStoredUser()])
      .then(([active, storedUser]) => {
        setSignedIn(active);
        setUser(storedUser);
      })
      .finally(() => setBooting(false));
  }, []);

  const refreshUser = useCallback(async () => {
    if (!signedIn) return;
    const nextUser = await apiRequest<User>('/api/v1/users/me');
    setUser(nextUser);
    await setStoredUser(nextUser);
  }, [signedIn]);

  const value = useMemo<SessionContextValue>(() => ({
    booting,
    signedIn,
    user,
    login: async (email, password) => {
      const payload = await authApi.login(email, password);
      setUser(payload.user);
      setSignedIn(true);
    },
    register: async (fullName, email, password) => {
      const payload = await authApi.register(fullName, email, password);
      setUser(payload.user);
      setSignedIn(true);
    },
    logout: async () => {
      await authApi.logout();
      setSignedIn(false);
      setUser(null);
    },
    refreshUser,
    updateLocalUser: async (nextUser) => {
      setUser(nextUser);
      await setStoredUser(nextUser);
    },
  }), [booting, refreshUser, signedIn, user]);

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const value = useContext(SessionContext);
  if (!value) throw new Error('useSession must be used inside SessionProvider');
  return value;
}
