# Extension Resilience Testing Plan

The browser extension is the most fragile component of Capsule because it relies on third-party DOM structures. We need a comprehensive testing plan to validate its resilience.

## 1. Automated DOM Mutation Testing
**Goal:** Prove adapters can handle unexpected DOM changes.
- **Method:** Use Playwright to load saved HTML snapshots of ChatGPT, Claude, and Gemini.
- **Mutation Engine:** Randomly rename utility classes (e.g., Tailwind classes), inject wrapper `<div>`s, and remove non-essential attributes.
- **Assertion:** The adapter's fallback strategies (Strategy 2 & 3) must successfully extract the conversation despite the mutations.

##important##
DOM Mutation can trriger Content script multiple times. We need to handle this, along with breaking the network paths if CORS is not supported.

## 2. Lazy Rendering & Infinite Scroll
**Goal:** Prove the content script captures full history, even when virtualized.
- **Method:** Simulate scrolling. The adapter must hook into the DOM scroll events or use `MutationObserver` to capture messages as they render, storing them in local state before the final extraction payload is sent.
- **Assertion:** Extracted message count matches the known total, not just the currently visible nodes.

IMPORTANT : 
A single user action can easily trigger 5–10 network hops.
Main aim to focus on are : 
Reduce round trips.
Batch requests when possible.
Cache frequently accessed data.
Avoid unnecessary API calls.-------> But how can we avoid unnecessary API calls in a browser extension,and more over how do i classify a API call as necessary or unnecessary.



## 3. Partial Render Recovery (Streaming Responses)
**Goal:** Ensure incomplete LLM generations aren't captured as final context.
- **Method:** Intercept extraction if a "Stop Generating" or streaming indicator is present.
- **Assertion:** The capture button should either be disabled or warn the user if extraction is attempted during active streaming.

## 4. Execution Plan
Phase 2 will introduce an `extension/tests/resilience/` directory with Playwright tests validating these exact scenarios against mock DOMs.


How about using srialization ?