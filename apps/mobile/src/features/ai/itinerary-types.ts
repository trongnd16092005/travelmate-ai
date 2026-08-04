export type ItineraryRequest = {
  destination?: string;
  startDate?: string;
  endDate?: string;
  durationDays?: number;
  numPeople?: number;
  budgetVnd?: number;
  preferences: string[];
  notes?: string;
};

export type ItineraryActivity = {
  period: 'morning' | 'afternoon' | 'evening';
  title: string;
  placeName?: string | null;
  notes?: string | null;
};

export type ItineraryDay = {
  day: number;
  title: string;
  activities: ItineraryActivity[];
};

export type BudgetBreakdown = {
  accommodationVnd: number;
  foodVnd: number;
  transportVnd: number;
  activitiesVnd: number;
  reserveVnd: number;
  totalVnd: number;
};

export type ItineraryPlan = {
  destination: string;
  durationDays: number;
  numPeople: number;
  summary: string;
  assumptions: string[];
  days: ItineraryDay[];
  budget: BudgetBreakdown;
};

export type ItineraryResponse = {
  status: 'needs_clarification' | 'ready';
  missingFields: ('destination' | 'durationDays' | 'numPeople' | 'budgetVnd')[];
  questions: string[];
  plan?: ItineraryPlan | null;
  provider?: 'mock' | 'gemini' | 'local' | null;
};
