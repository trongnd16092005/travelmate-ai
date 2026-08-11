import Constants from 'expo-constants';
import * as SecureStore from 'expo-secure-store';

const debuggerHost = Constants.expoConfig?.hostUri?.split(':')[0];
export const API_URL = (
  process.env.EXPO_PUBLIC_API_URL ??
  (debuggerHost ? `http://${debuggerHost}:8080` : 'http://127.0.0.1:8080')
).replace(/\/$/, '');

export type User = {
  id: number;
  fullName: string;
  email: string;
  avatarUrl?: string | null;
  bio?: string | null;
  role: string;
  travelStyle?: string | null;
  emailVerified?: boolean;
};

export type Trip = {
  id: number;
  name: string;
  destination: string;
  coverImageUrl?: string | null;
  startDate: string;
  endDate: string;
  budget: number;
  numPeople: number;
  status: string;
  travelStyle?: string | null;
  myRole: string;
  memberCount: number;
  durationDays: number;
};

export type TripMember = {
  memberId: number;
  userId: number;
  fullName: string;
  email?: string | null;
  avatarUrl?: string | null;
  role: 'OWNER' | 'EDITOR' | 'VIEWER';
  joinedAt: string;
};

export type TripDetail = Omit<Trip, 'memberCount' | 'myRole'> & {
  description?: string | null;
  myRole?: 'OWNER' | 'EDITOR' | 'VIEWER' | null;
  isPublic: boolean;
  publicToken?: string | null;
  owner: {
    id: number;
    fullName: string;
    avatarUrl?: string | null;
  };
  members: TripMember[];
  createdAt: string;
};

export type TripInvitation = {
  id: number;
  inviteeEmail: string;
  role: 'EDITOR' | 'VIEWER';
  status: 'PENDING' | 'ACCEPTED' | 'DECLINED' | 'EXPIRED';
  expiresAt: string;
};

export type Activity = {
  id: number;
  name: string;
  type: string;
  status: string;
  startTime?: string | null;
  endTime?: string | null;
  estimatedCost?: number | null;
  description?: string | null;
  note?: string | null;
  place?: { name: string; address?: string; rating?: number } | null;
};

export type ItineraryDay = {
  id: number;
  dayNumber: number;
  date: string;
  note?: string | null;
  activities: Activity[];
  totalEstimatedCost: number;
};

export type Itinerary = {
  tripId: number;
  days: ItineraryDay[];
  totalEstimatedCost: number;
};

export type Expense = {
  id: number;
  name: string;
  amount: number;
  category: string;
  expenseDate: string;
  paidBy: { id: number; fullName: string; avatarUrl?: string | null };
  note?: string | null;
};

export type ExpenseSummary = {
  totalExpense: number;
  budget: number;
  budgetUsedPercent: number;
  byCategory: Record<string, number>;
  recentExpenses: Expense[];
};

export type PlaceSuggestion = {
  id?: string;
  name: string;
  category?: string;
  description?: string;
  reason?: string;
  address?: string | null;
  estimatedCostVnd?: number;
  latitude?: number | null;
  longitude?: number | null;
  mapUrl?: string | null;
  imageUrl?: string | null;
  source?: string | null;
};

export type PlaceSuggestionResponse = {
  city: string;
  suggestions: PlaceSuggestion[];
  message: string;
  provider: 'mock' | 'gemini' | 'groq' | 'local' | 'catalog';
};

export type ChatResponse = {
  conversationId: number;
  messageId: number;
  reply: string;
  isOutOfScope: boolean;
  suggestedQuestions: string[];
  createdAt: string;
};

export type AuthPayload = {
  accessToken: string;
  refreshToken: string;
  user: User;
};

type ApiEnvelope<T> = {
  success: boolean;
  data: T;
  message?: string;
  error?: { code?: string; message?: string };
};

const ACCESS_KEY = 'travelmate_access_token';
const REFRESH_KEY = 'travelmate_refresh_token';
const USER_KEY = 'travelmate_user';

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export async function getStoredUser(): Promise<User | null> {
  const raw = await SecureStore.getItemAsync(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export async function hasSession() {
  return Boolean(await SecureStore.getItemAsync(ACCESS_KEY));
}

export async function clearSession() {
  await Promise.all([
    SecureStore.deleteItemAsync(ACCESS_KEY),
    SecureStore.deleteItemAsync(REFRESH_KEY),
    SecureStore.deleteItemAsync(USER_KEY),
  ]);
}

export async function setStoredUser(user: User) {
  await SecureStore.setItemAsync(USER_KEY, JSON.stringify(user));
}

async function saveSession(payload: AuthPayload) {
  await Promise.all([
    SecureStore.setItemAsync(ACCESS_KEY, payload.accessToken),
    SecureStore.setItemAsync(REFRESH_KEY, payload.refreshToken),
    SecureStore.setItemAsync(USER_KEY, JSON.stringify(payload.user)),
  ]);
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = await SecureStore.getItemAsync(REFRESH_KEY);
  if (!refreshToken) return null;
  const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refreshToken }),
  });
  if (!response.ok) {
    await clearSession();
    return null;
  }
  const envelope = (await response.json()) as ApiEnvelope<{ accessToken: string }>;
  const accessToken = envelope.data?.accessToken;
  if (!accessToken) {
    await clearSession();
    return null;
  }
  await SecureStore.setItemAsync(ACCESS_KEY, accessToken);
  return accessToken;
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  retry = true,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has('Content-Type') && options.body) headers.set('Content-Type', 'application/json');
  const token = await SecureStore.getItemAsync(ACCESS_KEY);
  if (token) headers.set('Authorization', `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch {
    throw new ApiError(`Không thể kết nối Core API tại ${API_URL}. Hãy kiểm tra Wi-Fi và địa chỉ máy chủ.`, 0, 'NETWORK_ERROR');
  }

  if (response.status === 401 && retry && (await refreshAccessToken())) {
    return apiRequest<T>(path, options, false);
  }

  let envelope: ApiEnvelope<T> | undefined;
  try {
    envelope = (await response.json()) as ApiEnvelope<T>;
  } catch {
    // Empty responses still use the HTTP status below.
  }
  if (!response.ok || envelope?.success === false) {
    throw new ApiError(
      envelope?.error?.message ?? envelope?.message ?? 'TravelMate chưa thể xử lý yêu cầu này.',
      response.status,
      envelope?.error?.code,
    );
  }
  return envelope?.data as T;
}

export const authApi = {
  async login(email: string, password: string) {
    const payload = await apiRequest<AuthPayload>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
    });
    await saveSession(payload);
    return payload;
  },

  async register(fullName: string, email: string, password: string) {
    await apiRequest<unknown>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ fullName: fullName.trim(), email: email.trim().toLowerCase(), password, confirmPassword: password }),
    });
    return this.login(email, password);
  },

  async logout() {
    const refreshToken = await SecureStore.getItemAsync(REFRESH_KEY);
    try {
      if (refreshToken) {
        await apiRequest('/api/v1/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refreshToken }),
        });
      }
    } finally {
      await clearSession();
    }
  },
};

export function parseJsonData<T>(value: string | T): T {
  return typeof value === 'string' ? (JSON.parse(value) as T) : value;
}

export function formatMoney(value: number | string | null | undefined) {
  return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 0 }).format(Number(value ?? 0))} ₫`;
}

export function formatCompactMoney(value: number | string | null | undefined) {
  const amount = Number(value ?? 0);
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toLocaleString('vi-VN', { maximumFractionDigits: 1 })} triệu`;
  if (amount >= 1_000) return `${Math.round(amount / 1_000)}K`;
  return `${amount.toLocaleString('vi-VN')} ₫`;
}

export function formatDate(value: string) {
  return new Intl.DateTimeFormat('vi-VN', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(`${value}T00:00:00`));
}

export function initials(name?: string) {
  return (name ?? 'TM').split(/\s+/).slice(-2).map((part) => part[0]?.toUpperCase()).join('');
}
