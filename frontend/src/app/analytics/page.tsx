"use client";

import { ActivitySquare, Database, Zap, ShieldCheck } from "lucide-react";

const mockTelemetry = {
  totalSearches: 124,
  averageLatencyMs: 342,
  successRate: 98.4,
  activeProjects: 3,
};

export default function AnalyticsPage() {
  return (
    <div className="p-10 max-w-5xl mx-auto space-y-12 bg-white h-full">
      <header>
        <h1 className="text-[28px] font-semibold tracking-tight text-zinc-900">Settings & Telemetry</h1>
        <p className="text-zinc-500 mt-1.5 text-sm">Monitor system health, connection status, and retrieval latencies.</p>
      </header>

      <section>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-4">Core Metrics</h2>
        <div className="flex gap-12 border-y border-zinc-100 py-6">
          <div className="flex flex-col">
            <span className="text-3xl font-light text-zinc-900">{mockTelemetry.totalSearches}</span>
            <span className="text-sm font-medium text-zinc-500 mt-1 flex items-center gap-1.5">
              <ActivitySquare className="w-3.5 h-3.5 text-zinc-400" /> Searches
            </span>
          </div>
          <div className="w-px bg-zinc-100" />
          <div className="flex flex-col">
            <span className="text-3xl font-light text-zinc-900">{mockTelemetry.averageLatencyMs}ms</span>
            <span className="text-sm font-medium text-zinc-500 mt-1 flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-zinc-400" /> Avg Latency
            </span>
          </div>
          <div className="w-px bg-zinc-100" />
          <div className="flex flex-col">
            <span className="text-3xl font-light text-zinc-900">{mockTelemetry.successRate}%</span>
            <span className="text-sm font-medium text-zinc-500 mt-1 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-zinc-400" /> Hit Rate
            </span>
          </div>
          <div className="w-px bg-zinc-100" />
          <div className="flex flex-col">
            <span className="text-3xl font-light text-zinc-900">{mockTelemetry.activeProjects}</span>
            <span className="text-sm font-medium text-zinc-500 mt-1 flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-zinc-400" /> Active Projects
            </span>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-4 font-mono">System Matrix</h2>
        <div className="h-64 rounded-2xl border border-zinc-100 bg-zinc-50/50 flex items-center justify-center">
          <p className="text-zinc-400 font-mono text-xs">Traffic Visualization Matrix Offline</p>
        </div>
      </section>
    </div>
  );
}
