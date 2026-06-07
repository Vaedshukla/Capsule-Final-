import { ExtractedMessage, ProviderAdapter } from './base';

export class ChatGPTAdapter implements ProviderAdapter {
  id = 'chatgpt';

  matches(hostname: string): boolean {
    return hostname.includes('chatgpt.com');
  }

  extractMessages(document: Document): ExtractedMessage[] {
    const elements = document.querySelectorAll('[data-message-author-role]');
    return Array.from(elements).map((el, index) => {
      const role = el.getAttribute('data-message-author-role');
      const content = el.textContent || '';
      return {
        role: role === 'user' ? 'user' : 'assistant',
        content: content.trim(),
        position: index + 1
      };
    }).filter(msg => msg.content.length > 0);
  }
}
