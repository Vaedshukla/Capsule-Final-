"use client";

import { useQuery } from "@tanstack/react-query";
import { capsuleApi } from "@/lib/api";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BrainCircuit, Clock } from "lucide-react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";

export default function ProjectDetailsPage() {
  const params = useParams();
  const id = params.id as string;

  const { data: projects = [] } = useQuery({
    queryKey: ["projects"],
    queryFn: capsuleApi.getProjects,
  });

  const project = projects.find((p) => p.id === id);

  const { data: capsules = [], isLoading } = useQuery({
    queryKey: ["capsules", id],
    queryFn: () => capsuleApi.getCapsules(id),
  });

  if (!project) return null;

  return (
    <div className="p-10 max-w-5xl mx-auto space-y-12 bg-white h-full">
      <header>
        <h1 className="text-[28px] font-semibold tracking-tight text-zinc-900">{project.name}</h1>
        <p className="text-zinc-500 mt-1.5 text-sm max-w-2xl">{project.description || "No description provided."}</p>
      </header>

      <section className="space-y-6 pt-2">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-4 flex items-center gap-2">
          <BrainCircuit className="w-3.5 h-3.5 text-indigo-400" />
          Project Memory Capsules
        </h2>
        
        {isLoading ? (
          <div className="text-zinc-400 text-sm animate-pulse font-medium">Loading capsules...</div>
        ) : (
          <div className="divide-y divide-zinc-100/80 border-t border-zinc-100/80">
            {capsules.map((capsule: any) => (
              <Link key={capsule.id} href={`/conversations/${capsule.conversation_id}`} className="block py-6 group hover:bg-zinc-50/50 transition-colors -mx-4 px-4 rounded-xl">
                <div className="flex items-start gap-4">
                  <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-zinc-300 group-hover:bg-indigo-400 transition-colors" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1.5">
                      <h3 className="text-lg font-semibold text-zinc-900 group-hover:text-indigo-600 transition-colors">
                        {capsule.title || "Untitled Capsule"}
                      </h3>
                      <span className="text-xs text-zinc-400 font-medium whitespace-nowrap">
                        {formatDistanceToNow(new Date(capsule.created_at), { addSuffix: true })}
                      </span>
                    </div>
                    <p className="text-sm text-zinc-500 line-clamp-2 leading-relaxed max-w-3xl">{capsule.summary}</p>
                    <div className="mt-3 flex gap-2">
                       <span className="inline-flex items-center text-[10px] uppercase tracking-wider font-semibold text-indigo-500" title="Calculated by the AI based on the density of decisions and insights extracted.">
                         Importance: {(capsule.importance_score * 10).toFixed(1)}/10
                       </span>
                    </div>
                  </div>
                </div>
              </Link>
            ))}

            {capsules.length === 0 && (
              <div className="py-16 text-center text-zinc-400 text-sm">
                No conversations have been captured for this project yet.
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
