"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { capsuleApi } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search, BrainCircuit, MessageSquare, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function MemoryExplorerPage() {
  const [query, setQuery] = useState("");
  const [searchTrigger, setSearchTrigger] = useState("");

  const { data: searchResponse, isLoading } = useQuery({
    queryKey: ["search", searchTrigger],
    queryFn: () => capsuleApi.search(searchTrigger, undefined, 20),
    enabled: !!searchTrigger,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) setSearchTrigger(query);
  };

  return (
    <div className="p-10 max-w-4xl mx-auto space-y-12 bg-white h-full">
      <div className="text-center space-y-4 py-12">
        <h1 className="text-[32px] font-semibold tracking-tight text-zinc-900">Memory Explorer</h1>
        <p className="text-sm text-zinc-500 max-w-lg mx-auto">
          Semantically search across all extracted decisions, risks, and raw conversations.
        </p>
        
        <form onSubmit={handleSearch} className="max-w-2xl mx-auto mt-8 relative">
          <Input 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., Why did we choose PostgreSQL over MongoDB?"
            className="h-13 pl-12 pr-28 bg-zinc-50 border-zinc-200 focus:bg-white focus:border-zinc-300 focus-visible:ring-1 focus-visible:ring-zinc-200 text-base rounded-xl shadow-none text-zinc-900 placeholder:text-zinc-400 transition-all"
          />
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400 w-4 h-4" />
          <Button 
            type="submit" 
            disabled={!query.trim() && !isLoading}
            className="absolute right-1.5 top-1/2 -translate-y-1/2 h-10 px-5 bg-zinc-900 hover:bg-zinc-800 disabled:bg-zinc-100 disabled:text-zinc-400 text-white rounded-lg font-medium text-xs shadow-none border-0 transition-colors cursor-pointer disabled:cursor-not-allowed"
          >
            {isLoading ? "Searching..." : "Search"}
          </Button>
        </form>
      </div>

      {searchTrigger && (
        <div className="max-w-2xl mx-auto space-y-6">
          <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
              {isLoading ? "Searching memories..." : `Found ${searchResponse?.results.length || 0} results`}
            </h2>
          </div>

          <div className="divide-y divide-zinc-100/80">
            {searchResponse?.results.map((result, i) => (
              <div key={result.id + i} className="py-6 first:pt-0 last:pb-0 flex gap-6 items-start">
                <div className="w-10 h-10 rounded-full bg-zinc-50 flex items-center justify-center shrink-0 border border-zinc-100">
                  {result.type === 'capsule' ? (
                    <BrainCircuit className="w-4 h-4 text-indigo-500" />
                  ) : (
                    <MessageSquare className="w-4 h-4 text-emerald-500" />
                  )}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-4 mb-2">
                    <h3 className="text-base font-semibold text-zinc-900">{result.title || 'Untitled Context'}</h3>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold text-zinc-400 uppercase">
                        Score: {(result.similarity_score * 100).toFixed(1)}%
                      </span>
                      <span className="text-[10px] font-semibold text-zinc-500 px-2 py-0.5 rounded-full bg-zinc-50 border border-zinc-150">
                        {result.type.toUpperCase()}
                      </span>
                    </div>
                  </div>

                  <p className="text-zinc-600 text-sm leading-relaxed whitespace-pre-wrap mb-4">
                    {result.content}
                  </p>
                  
                  <div className="flex items-center justify-between pt-2">
                    <div className="flex gap-2">
                      {result.source_slug && (
                        <span className="inline-flex items-center text-[10px] font-medium text-zinc-500 bg-zinc-50 px-2 py-0.5 rounded border border-zinc-100">{result.source_slug}</span>
                      )}
                    </div>
                    {result.conversation_id && (
                      <Link href={`/conversations/${result.conversation_id}`}>
                        <Button variant="link" size="sm" className="text-indigo-600 hover:text-indigo-700 font-medium text-xs p-0 h-auto">
                          View Conversation <ArrowRight className="ml-1 w-3 h-3 inline" />
                        </Button>
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
