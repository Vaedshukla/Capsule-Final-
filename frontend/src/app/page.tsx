"use client";

import { useQuery } from "@tanstack/react-query";
import { capsuleApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FolderOpen, BrainCircuit, MessageSquare, Clock } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import Link from "next/link";

export default function DashboardOverview() {
  const { data: projects = [] } = useQuery({
    queryKey: ["projects"],
    queryFn: capsuleApi.getProjects,
  });

  const { data: capsules = [] } = useQuery({
    queryKey: ["capsules"],
    queryFn: () => capsuleApi.getCapsules(),
  });

  const totalConversations = capsules.length; // 1 capsule per conversation for now

  return (
    <div className="p-10 max-w-5xl mx-auto space-y-12 bg-white h-full">
      <header>
        <h1 className="text-[28px] font-semibold tracking-tight text-zinc-900">Overview</h1>
        <p className="text-zinc-500 mt-1.5 text-sm">Welcome back. Here's a snapshot of your memory state.</p>
      </header>

      <section>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-4">At a glance</h2>
        <div className="flex gap-12 border-y border-zinc-100 py-6">
          <div className="flex flex-col">
            <span className="text-3xl font-light text-zinc-900">{projects.length}</span>
            <span className="text-sm font-medium text-zinc-500 mt-1 flex items-center gap-1.5"><FolderOpen className="w-3.5 h-3.5 text-zinc-400" /> Projects</span>
          </div>
          <div className="w-px bg-zinc-100" />
          <div className="flex flex-col">
            <span className="text-3xl font-light text-zinc-900">{capsules.length}</span>
            <span className="text-sm font-medium text-zinc-500 mt-1 flex items-center gap-1.5"><BrainCircuit className="w-3.5 h-3.5 text-zinc-400" /> Capsules</span>
          </div>
          <div className="w-px bg-zinc-100" />
          <div className="flex flex-col">
            <span className="text-3xl font-light text-zinc-900">{totalConversations}</span>
            <span className="text-sm font-medium text-zinc-500 mt-1 flex items-center gap-1.5"><MessageSquare className="w-3.5 h-3.5 text-zinc-400" /> Conversations</span>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-4">Recent Activity</h2>
        <div className="divide-y divide-zinc-100/80">
          {capsules.slice(0, 5).map((capsule) => {
            const project = projects.find(p => p.id === (capsule as any).project_id);
            return (
              <Link key={capsule.id} href={`/conversations/${(capsule as any).conversation_id}`} className="block py-4 group hover:bg-zinc-50/50 transition-colors -mx-4 px-4 rounded-xl">
                <div className="flex items-start gap-4">
                  <div className="mt-1 w-2 h-2 rounded-full bg-zinc-300 group-hover:bg-indigo-400 transition-colors" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-semibold text-zinc-900 truncate pr-4 group-hover:text-indigo-600 transition-colors">{capsule.title || "Untitled Capsule"}</h3>
                      <span className="text-xs text-zinc-400 font-medium whitespace-nowrap">
                        {formatDistanceToNow(new Date(capsule.created_at), { addSuffix: true })}
                      </span>
                    </div>
                    <p className="text-sm text-zinc-500 line-clamp-2 leading-relaxed">{capsule.summary}</p>
                    {project && (
                      <div className="mt-2.5 inline-flex items-center gap-1.5 text-xs font-medium text-zinc-500 group-hover:text-zinc-700 transition-colors">
                        <FolderOpen className="w-3 h-3" /> {project.name}
                      </div>
                    )}
                  </div>
                </div>
              </Link>
            );
          })}
          {capsules.length === 0 && (
            <div className="py-12 text-zinc-400 text-sm">
              No memory capsules generated yet. Capture a conversation to get started.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
