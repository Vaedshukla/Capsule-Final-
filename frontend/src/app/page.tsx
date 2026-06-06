"use client";

import { useState, useEffect, useCallback } from "react";
import { capsuleApi, Project, Capsule, SearchResult } from "@/lib/api";

// ─── Source Platform Icons ─────────────────────────────────────────────────
const SOURCE_COLORS: Record<string, string> = {
  chatgpt: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  claude: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  gemini: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  cursor: "bg-violet-500/20 text-violet-300 border-violet-500/30",
  unknown: "bg-gray-500/20 text-gray-300 border-gray-500/30",
};

// ─── Components ────────────────────────────────────────────────────────────

function Sidebar({
  projects,
  activeProject,
  onSelectProject,
  onNewProject,
}: {
  projects: Project[];
  activeProject: string | null;
  onSelectProject: (id: string | null) => void;
  onNewProject: () => void;
}) {
  return (
    <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-sm">C</div>
          <div>
            <div className="text-sm font-semibold text-white">Project Capsule</div>
            <div className="text-xs text-gray-500">Memory Dashboard</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="text-xs font-medium text-gray-500 uppercase tracking-wider px-2 mb-2">Projects</div>
        <button
          onClick={() => onSelectProject(null)}
          className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
            activeProject === null
              ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30"
              : "text-gray-400 hover:text-white hover:bg-gray-800"
          }`}
        >
          All Memory
        </button>
        {projects.map((p) => (
          <button
            key={p.id}
            onClick={() => onSelectProject(p.id)}
            className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center gap-2 ${
              activeProject === p.id
                ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30"
                : "text-gray-400 hover:text-white hover:bg-gray-800"
            }`}
          >
            {p.color && (
              <span
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: p.color }}
              />
            )}
            <span className="truncate">{p.name}</span>
          </button>
        ))}
        <button
          onClick={onNewProject}
          className="w-full text-left px-3 py-2 rounded-lg text-sm text-gray-500 hover:text-white hover:bg-gray-800 transition-colors flex items-center gap-2"
        >
          <span>＋</span> New Project
        </button>
      </nav>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-gray-800">
        <div className="text-xs text-gray-600">v0.1.0 · Local Mode</div>
      </div>
    </aside>
  );
}

function CapsuleCard({ capsule }: { capsule: Capsule }) {
  const [expanded, setExpanded] = useState(false);
  const score = Math.round(capsule.importance_score * 100);

  return (
    <div
      className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-indigo-500/40 transition-all cursor-pointer"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <div
              className="w-2 h-2 rounded-full flex-shrink-0"
              style={{
                backgroundColor: `hsl(${score * 1.2}, 70%, 55%)`,
              }}
            />
            <h3 className="text-sm font-medium text-white truncate">{capsule.title}</h3>
          </div>
          <p className="text-xs text-gray-400 line-clamp-2">{capsule.summary}</p>
        </div>
        <div className="flex flex-col items-end gap-1 flex-shrink-0">
          <span className="text-xs font-mono text-indigo-400">{score}%</span>
          <span className="text-xs text-gray-600">{capsule.access_count} uses</span>
        </div>
      </div>

      {expanded && (
        <div className="mt-3 pt-3 border-t border-gray-800 space-y-2">
          <div>
            <div className="text-xs font-medium text-gray-500 mb-1">Summary</div>
            <p className="text-xs text-gray-300 whitespace-pre-wrap">{capsule.summary}</p>
          </div>
          {capsule.decisions && (() => {
            try {
              const d = JSON.parse(capsule.decisions);
              return d.length > 0 ? (
                <div>
                  <div className="text-xs font-medium text-amber-500 mb-1">Key Decisions</div>
                  <ul className="space-y-1">
                    {d.slice(0, 5).map((dec: string, i: number) => (
                      <li key={i} className="text-xs text-gray-300 flex gap-2">
                        <span className="text-amber-500 flex-shrink-0">→</span>
                        <span>{dec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null;
            } catch { return null; }
          })()}
          <div className="text-xs text-gray-600">
            Created {new Date(capsule.created_at).toLocaleDateString()}
          </div>
        </div>
      )}
    </div>
  );
}

function SearchBar({ onSearch }: { onSearch: (q: string) => void }) {
  const [value, setValue] = useState("");

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); if (value.trim()) onSearch(value.trim()); }}
      className="relative"
    >
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder='Search memory… e.g. "auth system decisions"'
        className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 pl-10 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors"
      />
      <svg className="absolute left-3 top-3.5 w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <button
        type="submit"
        className="absolute right-2 top-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-3 py-1.5 rounded-lg transition-colors"
      >
        Search
      </button>
    </form>
  );
}

function SearchResultCard({ result }: { result: SearchResult }) {
  const slug = result.source_slug || "unknown";
  const colorClass = SOURCE_COLORS[slug] || SOURCE_COLORS.unknown;
  const similarity = Math.round(result.similarity_score * 100);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className={`text-xs px-2 py-0.5 rounded-full border ${colorClass}`}>
          {result.type === "capsule" ? "📦 Capsule" : "💬 Message"}
        </span>
        {slug !== "unknown" && (
          <span className={`text-xs px-2 py-0.5 rounded-full border ${colorClass}`}>{slug}</span>
        )}
        <span className="ml-auto text-xs font-mono text-indigo-400">{similarity}% match</span>
      </div>
      <h4 className="text-sm font-medium text-white mb-1">{result.title}</h4>
      <p className="text-xs text-gray-400 line-clamp-3">{result.content}</p>
    </div>
  );
}

// ─── Main Dashboard ─────────────────────────────────────────────────────────

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [capsules, setCapsules] = useState<Capsule[]>([]);
  const [activeProject, setActiveProject] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[] | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [backendStatus, setBackendStatus] = useState<"unknown" | "online" | "offline">("unknown");
  const [activeTab, setActiveTab] = useState<"capsules" | "search">("capsules");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [ps, cs] = await Promise.all([
        capsuleApi.getProjects(),
        capsuleApi.getCapsules(activeProject ?? undefined),
      ]);
      setProjects(ps);
      setCapsules(cs);
    } catch {
      setBackendStatus("offline");
    } finally {
      setLoading(false);
    }
  }, [activeProject]);

  useEffect(() => {
    capsuleApi.health()
      .then(() => setBackendStatus("online"))
      .catch(() => setBackendStatus("offline"));
    loadData();
  }, [loadData]);

  const handleSearch = async (q: string) => {
    setSearchQuery(q);
    setActiveTab("search");
    try {
      const res = await capsuleApi.search(q, activeProject ?? undefined);
      setSearchResults(res.results);
    } catch {
      setSearchResults([]);
    }
  };

  const handleNewProject = async () => {
    const name = window.prompt("Project name:");
    if (!name?.trim()) return;
    await capsuleApi.createProject({ name });
    loadData();
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        projects={projects}
        activeProject={activeProject}
        onSelectProject={(id) => { setActiveProject(id); setSearchResults(null); }}
        onNewProject={handleNewProject}
      />

      <main className="flex-1 overflow-y-auto">
        {/* Top Bar */}
        <div className="sticky top-0 z-10 bg-gray-950/80 backdrop-blur border-b border-gray-800 px-6 py-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h1 className="text-lg font-semibold text-white">
                {activeProject ? projects.find(p => p.id === activeProject)?.name : "All Memory"}
              </h1>
              <p className="text-xs text-gray-500">
                {capsules.length} capsule{capsules.length !== 1 ? "s" : ""} ·{" "}
                <span className={backendStatus === "online" ? "text-emerald-400" : "text-red-400"}>
                  {backendStatus === "online" ? "● Backend Online" : "● Backend Offline"}
                </span>
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => { setActiveTab("capsules"); setSearchResults(null); }}
                className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${activeTab === "capsules" ? "bg-indigo-600 text-white" : "text-gray-400 hover:text-white hover:bg-gray-800"}`}
              >
                Capsules
              </button>
              <button
                onClick={() => setActiveTab("search")}
                className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${activeTab === "search" ? "bg-indigo-600 text-white" : "text-gray-400 hover:text-white hover:bg-gray-800"}`}
              >
                Search
              </button>
            </div>
          </div>
          <SearchBar onSearch={handleSearch} />
        </div>

        <div className="px-6 py-6">
          {/* Backend Offline Banner */}
          {backendStatus === "offline" && (
            <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-sm text-red-300">
              <strong>Backend offline.</strong> Start the Capsule backend at{" "}
              <code className="text-red-200">http://localhost:8000</code> to use the dashboard.
            </div>
          )}

          {/* Capsules Tab */}
          {activeTab === "capsules" && (
            <>
              {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {[...Array(6)].map((_, i) => (
                    <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-4 animate-pulse h-28" />
                  ))}
                </div>
              ) : capsules.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-24 text-center">
                  <div className="text-5xl mb-4">📦</div>
                  <h2 className="text-lg font-medium text-white mb-2">No memory capsules yet</h2>
                  <p className="text-sm text-gray-500 max-w-sm">
                    Install the Capsule browser extension, capture an AI conversation, then compress it into a capsule.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {capsules.map((c) => <CapsuleCard key={c.id} capsule={c} />)}
                </div>
              )}
            </>
          )}

          {/* Search Tab */}
          {activeTab === "search" && (
            <div className="space-y-4">
              {searchQuery && (
                <p className="text-sm text-gray-500">
                  Results for <span className="text-white font-medium">"{searchQuery}"</span>
                  {searchResults && ` · ${searchResults.length} found`}
                </p>
              )}
              {searchResults === null ? (
                <div className="flex flex-col items-center justify-center py-24 text-center">
                  <div className="text-5xl mb-4">🔍</div>
                  <p className="text-sm text-gray-500">Use the search bar above to query your AI memory.</p>
                </div>
              ) : searchResults.length === 0 ? (
                <div className="text-center py-16 text-gray-500">No results found for "{searchQuery}"</div>
              ) : (
                <div className="space-y-3">
                  {searchResults.map((r) => <SearchResultCard key={r.id} result={r} />)}
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
