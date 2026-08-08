import { create } from 'axios';

import { env } from '@/config/env';

export const aiClient = create({
  baseURL: env.aiServiceUrl,
  timeout: 120_000,
  headers: {
    'Content-Type': 'application/json',
  },
});
