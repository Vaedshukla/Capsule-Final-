import { ExtractedMessage, ProviderAdapter } from './base';

export class ClaudeAdapter implements ProviderAdapter {
  id = 'claude';

  matches(hostname: string): boolean {
    return hostname.includes('claude.ai');
  }

  extractMessages(document: Document): ExtractedMessage[] {
    // Claude uses generic nested divs, but typically `.font-user-message` and `.font-claude-message` 
    // are present, or `.prose` for Assistant and simple text blocks for User.
    // For this MVP heuristic, we look for '.font-user-message' and '.font-claude-message'.
    const elements = document.querySelectorAll('.font-user-message, .font-claude-message');
    
    if (elements.length > 0) {
      return Array.from(elements).map((el, index) => {
        const isUser = el.classList.contains('font-user-message');
        return {
          role: isUser ? 'user' : 'assistant',
          content: (el.textContent || '').trim(),
          position: index + 1
        };
      }).filter(msg => msg.content.length > 0);
    }

    // Fallback heuristic: Claude's newer DOM might just use generic blocks.
    // We search for elements with 'data-is-user' if they exist.
    const fallbackElements = document.querySelectorAll('[data-is-user]');
    if (fallbackElements.length > 0) {
      return Array.from(fallbackElements).map((el, index) => {
        const isUser = el.getAttribute('data-is-user') === 'true';
        return {
          role: isUser ? 'user' : 'assistant',
          content: (el.textContent || '').trim(),
          position: index + 1
        };
      }).filter(msg => msg.content.length > 0);
    }

    return [];
  }
}
