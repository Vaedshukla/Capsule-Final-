import { ExtractedMessage, ProviderAdapter } from './base';

export class GeminiAdapter implements ProviderAdapter {
  id = 'gemini';

  matches(hostname: string): boolean {
    return hostname.includes('gemini.google.com');
  }

  extractMessages(document: Document): ExtractedMessage[] {
    // Gemini typically uses specific tags like `user-query` and `model-response` 
    // or deep generic tags. We will use a heuristic looking for common block elements.
    const messages: ExtractedMessage[] = [];
    
    // Fallback heuristic: query all user queries and model responses if they exist in the DOM.
    // NOTE: Google changes these classes frequently. This is an MVP heuristic.
    const containerElements = document.querySelectorAll('user-query, model-response, .query-text, .response-text');
    
    if (containerElements.length > 0) {
      let position = 1;
      containerElements.forEach((el) => {
        const tagName = el.tagName.toLowerCase();
        const className = el.className.toLowerCase();
        const isUser = tagName === 'user-query' || className.includes('query');
        
        const content = (el.textContent || '').trim();
        if (content.length > 0) {
          messages.push({
            role: isUser ? 'user' : 'assistant',
            content,
            position: position++
          });
        }
      });
      return messages;
    }

    // Secondary fallback: sometimes it uses message bubbles
    const bubbles = document.querySelectorAll('.message-bubble');
    if (bubbles.length > 0) {
       return Array.from(bubbles).map((el, index) => {
         const isUser = el.classList.contains('user');
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
