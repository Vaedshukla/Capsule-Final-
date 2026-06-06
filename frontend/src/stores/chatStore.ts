import { create } from 'zustand'

export interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  provider?: str
  tokens_used?: number
  latency_ms?: number
  fallback_used?: boolean
}

export interface ProviderHealth {
  name: string
  status: 'HEALTHY' | 'DEGRADED' | 'RATE_LIMITED' | 'EXHAUSTED' | 'OFFLINE'
  latency: number
}

interface ChatState {
  messages: Message[]
  isStreaming: boolean
  activeProvider: string
  providerHealth: Record<string, ProviderHealth>
  
  // Actions
  addMessage: (msg: Message) => void
  setStreaming: (status: boolean) => void
  setActiveProvider: (provider: string) => void
  updateProviderHealth: (health: ProviderHealth) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatState>()((set) => ({
  messages: [],
  isStreaming: false,
  activeProvider: 'openai',
  providerHealth: {},

  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setStreaming: (status) => set({ isStreaming: status }),
  setActiveProvider: (provider) => set({ activeProvider: provider }),
  updateProviderHealth: (health) => set((state) => ({
    providerHealth: {
      ...state.providerHealth,
      [health.name]: health
    }
  })),
  clearMessages: () => set({ messages: [] })
}))
