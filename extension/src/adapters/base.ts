export interface ExtractedMessage {
  role: 'user' | 'assistant';
  content: string;
  position: number;
}

export interface ProviderAdapter {
  id: string;
  matches(hostname: string): boolean;
  extractMessages(document: Document): ExtractedMessage[];
}
