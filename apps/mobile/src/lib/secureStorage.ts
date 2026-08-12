const memoryStorage = new Map<string, string>();

function webStorage(): Storage | null {
  if (typeof globalThis.localStorage === 'undefined') return null;
  return globalThis.localStorage;
}

export async function getItemAsync(key: string): Promise<string | null> {
  try {
    return webStorage()?.getItem(key) ?? memoryStorage.get(key) ?? null;
  } catch {
    return memoryStorage.get(key) ?? null;
  }
}

export async function setItemAsync(key: string, value: string): Promise<void> {
  memoryStorage.set(key, value);
  try {
    webStorage()?.setItem(key, value);
  } catch {
    // The in-memory value keeps preview sessions working when storage is blocked.
  }
}

export async function deleteItemAsync(key: string): Promise<void> {
  memoryStorage.delete(key);
  try {
    webStorage()?.removeItem(key);
  } catch {
    // Nothing else to remove when storage is unavailable.
  }
}
