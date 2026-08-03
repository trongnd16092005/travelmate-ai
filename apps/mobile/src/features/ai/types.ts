export type ChatRole = 'user' | 'assistant';

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
};

export type ChatHistoryMessage = Pick<ChatMessage, 'role' | 'content'>;

export type TripContext = {
  destination: string;
  startDate?: string;
  endDate?: string;
  budgetVnd?: number;
  numPeople?: number;
};

export type ChatRequest = {
  message: string;
  history: ChatHistoryMessage[];
  tripContext?: TripContext;
};

export type ChatResponse = {
  reply: string;
  isOutOfScope: boolean;
  suggestedQuestions: string[];
  provider: 'mock' | 'gemini' | 'local';
};
