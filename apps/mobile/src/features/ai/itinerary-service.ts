import type { ItineraryRequest, ItineraryResponse } from '@/features/ai/itinerary-types';
import { aiClient } from '@/lib/api/ai-client';

export async function generateItinerary(
  request: ItineraryRequest,
): Promise<ItineraryResponse> {
  const response = await aiClient.post<ItineraryResponse>('/ai/itineraries/generate', request);
  return response.data;
}

