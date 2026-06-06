import { defineContentScript } from 'wxt/sandbox';

export default defineContentScript({
  matches: [
    'https://chatgpt.com/*',
    'https://claude.ai/*',
    'https://gemini.google.com/*'
  ],
  main() {
    console.log('[Capsule] Content script loaded on', window.location.hostname);

    chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
      if (message.type === 'CAPTURE_REQUEST') {
        try {
          const elements = document.querySelectorAll('[data-message-author-role]');
          const messages = Array.from(elements).map((el, index) => {
            const role = el.getAttribute('data-message-author-role');
            const content = el.textContent || '';
            return {
              role: role === 'user' ? 'user' : 'assistant',
              content: content,
              position: index + 1
            };
          });

          if (messages.length === 0) {
            sendResponse({ success: false, error: 'No messages found on page.' });
            return false;
          }

          let sourceSlug = 'unknown';
          if (window.location.hostname.includes('chatgpt.com')) sourceSlug = 'chatgpt';
          else if (window.location.hostname.includes('claude.ai')) sourceSlug = 'claude';
          else if (window.location.hostname.includes('gemini.google.com')) sourceSlug = 'gemini';

          sendResponse({
            success: true,
            data: {
              url: window.location.href,
              title: document.title,
              source: sourceSlug,
              messages: messages
            }
          });
        } catch (err: any) {
          sendResponse({ success: false, error: err.message });
        }
        return false;
      }
    });
  },
});
