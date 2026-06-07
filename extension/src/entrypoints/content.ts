import { defineContentScript } from 'wxt/sandbox';
import { adapters } from '../adapters';

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
          // 1. Find matching adapter
          const adapter = adapters.find(a => a.matches(window.location.hostname));
          
          if (!adapter) {
            sendResponse({ success: false, error: 'Unsupported AI platform' });
            return false;
          }

          // 2. Extract messages
          const messages = adapter.extractMessages(document);

          if (messages.length === 0) {
            sendResponse({ success: false, error: `No messages found. ${adapter.id} DOM structure may have changed.` });
            return false;
          }

          // 3. Return normalized payload
          sendResponse({
            success: true,
            data: {
              url: window.location.href,
              title: document.title,
              source: adapter.id,
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
