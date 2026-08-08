const apiUrl = process.env.EXPO_PUBLIC_API_URL;
const aiServiceUrl = process.env.EXPO_PUBLIC_AI_SERVICE_URL;

if (!apiUrl) {
  console.warn('EXPO_PUBLIC_API_URL chưa được cấu hình.');
}

if (!aiServiceUrl) {
  console.warn('EXPO_PUBLIC_AI_SERVICE_URL chưa được cấu hình.');
}

export const env = {
  apiUrl: apiUrl ?? 'http://localhost:8080/api/v1',
  aiServiceUrl: aiServiceUrl ?? 'http://localhost:8000/internal/v1',
};
