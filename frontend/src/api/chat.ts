import { apiClient } from './client';
import type { ChatMessage, ChatResponse } from '@/types/api';

/**
 * Send a chat request to the backend agent. The backend will process
 * messages and return a generated answer. If streaming is supported, this
 * function can be extended to handle event streams.
 */
export async function chat(messages: ChatMessage[]): Promise<ChatResponse> {
  const res = await apiClient.post<ChatResponse>('/api/v1/chat', {
    messages,
  });
  return res.data;
}