const apiUrl = process.env.EXPO_PUBLIC_API_URL;

if (!apiUrl) {
  console.warn('EXPO_PUBLIC_API_URL chưa được cấu hình.');
}

export const env = {
  apiUrl: apiUrl ?? 'http://localhost:8080/api/v1',
};
