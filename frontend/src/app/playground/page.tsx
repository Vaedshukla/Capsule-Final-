"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { capsuleApi } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Play } from "lucide-react";

export default function SearchPlaygroundPage() {
  const [query, setQuery] = useState("");
  const [searchTrigger, setSearchTrigger] = useState("");

  const { data: searchResponse, isLoading } = useQuery({
    queryKey: ["search", "playground", searchTrigger],
    queryFn: () => capsuleApi.search(searchTrigger, undefined, 50),
    enabled: !!searchTrigger,
  });

  return (
    <div className="p-10 h-full flex flex-col space-y-8 bg-white max-w-6xl mx-auto">
      <div>
        <h1 className="text-[28px] font-semibold tracking-tight text-zinc-900">Search Playground</h1>
        <p className="text-zinc-500 mt-1.5 text-sm">Test the hybrid retrieval algorithm and inspect raw ranking logic.</p>
      </div>

      <div className="flex gap-4">
        <Input 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter a test query..."
          className="font-mono bg-zinc-50 border-zinc-200/80 focus-visible:ring-zinc-400 h-11 text-zinc-900 text-sm rounded-lg"
          onKeyDown={(e) => e.key === 'Enter' && setQuery(query) && setSearchTrigger(query)}
        />
        <Button 
          onClick={() => setSearchTrigger(query)}
          disabled={!query || isLoading}
          className="h-11 px-5 bg-zinc-900 hover:bg-zinc-800 text-white rounded-lg font-medium text-xs border-0 shrink-0"
        >
          <Play className="w-3.5 h-3.5 mr-2 inline" /> Execute Query
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 flex-1 min-h-0">
        <div className="flex flex-col min-h-0 border border-zinc-100 rounded-2xl bg-white overflow-hidden">
          <div className="py-4 px-6 border-b border-zinc-100 bg-zinc-50/50 flex justify-between items-center">
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Results Ranking</span>
            <span className="text-xs font-medium text-zinc-500 bg-zinc-150/80 px-2 py-0.5 rounded-full">Total: {searchResponse?.total || 0}</span>
          </div>
          <ScrollArea className="flex-1 p-6">
            <div className="space-y-4">
              {searchResponse?.results.map((r, i) => (
                <div key={r.id + i} className="p-4 bg-zinc-50/50 rounded-xl border border-zinc-100 text-sm font-mono flex flex-col gap-2">
                  <div className="flex justify-between items-center text-xs text-zinc-400 border-b border-zinc-100/80 pb-2">
                    <span className="font-semibold">Rank #{i + 1}</span>
                    <span className="text-indigo-600 font-semibold">Score: {r.similarity_score.toFixed(4)}</span>
                  </div>
                  <div className="text-zinc-700 leading-relaxed">
                    <span className="text-indigo-600 font-semibold mr-1">[{r.type.toUpperCase()}]</span> {r.title || 'No Title'}
                  </div>
                </div>
              ))}
              {!isLoading && (!searchResponse || searchResponse.results.length === 0) && (
                <div className="text-zinc-400 text-center mt-12 text-sm font-medium">Run a query to see results.</div>
              )}
            </div>
          </ScrollArea>
        </div>

        <div className="flex flex-col min-h-0 border border-zinc-100 rounded-2xl bg-zinc-50/30 overflow-hidden">
          <div className="py-4 px-6 border-b border-zinc-100 bg-zinc-50/50">
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Raw JSON Output</span>
          </div>
          <ScrollArea className="flex-1">
            <pre className="p-6 text-xs font-mono text-zinc-500 whitespace-pre-wrap leading-relaxed">
              {isLoading ? "Executing query..." : JSON.stringify(searchResponse || { message: "Waiting for input..." }, null, 2)}
            </pre>
          </ScrollArea>
        </div>
      </div>
    </div>
  );
}
