import * as SecureStore from 'expo-secure-store';
import { create } from 'zustand';

const accessTokenKey = 'travelmate.accessToken';

type AuthState = {
  accessToken: string | null;
  setAccessToken: (token: string) => Promise<void>;
  clearSession: () => Promise<void>;
};

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  setAccessToken: async (token) => {
    await SecureStore.setItemAsync(accessTokenKey, token);
    set({ accessToken: token });
  },
  clearSession: async () => {
    await SecureStore.deleteItemAsync(accessTokenKey);
    set({ accessToken: null });
  },
}));
