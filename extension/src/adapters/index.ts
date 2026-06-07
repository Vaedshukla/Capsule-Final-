import { ChatGPTAdapter } from './chatgpt';
import { ClaudeAdapter } from './claude';
import { GeminiAdapter } from './gemini';
import { ProviderAdapter } from './base';

export const adapters: ProviderAdapter[] = [
  new ChatGPTAdapter(),
  new ClaudeAdapter(),
  new GeminiAdapter()
];

export * from './base';
