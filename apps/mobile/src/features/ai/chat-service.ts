import type { ChatRequest, ChatResponse } from '@/features/ai/types';
import { aiClient } from '@/lib/api/ai-client';

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await aiClient.post<ChatResponse>('/ai/chat', request);
  return response.data;
}
