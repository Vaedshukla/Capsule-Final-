"use client";

import { useQuery } from "@tanstack/react-query";
import { capsuleApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { FolderOpen, Plus } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function ProjectsPage() {
  const { data: projects = [], isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: capsuleApi.getProjects,
  });

  return (
    <div className="p-10 max-w-5xl mx-auto space-y-12 bg-white h-full">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-[28px] font-semibold tracking-tight text-zinc-900">Projects</h1>
          <p className="text-zinc-500 mt-1.5 text-sm">Manage workspaces and context boundaries.</p>
        </div>
        <Button className="bg-zinc-900 hover:bg-zinc-800 text-white border-0 shadow-sm rounded-lg font-medium px-5 h-10">
          <Plus className="w-4 h-4 mr-2" />
          New Project
        </Button>
      </header>

      {isLoading ? (
        <div className="space-y-6">
           <div className="h-24 w-full bg-zinc-50 border-y border-zinc-100 animate-pulse" />
           <div className="h-24 w-full bg-zinc-50 border-y border-zinc-100 animate-pulse" />
        </div>
      ) : (
        <div className="divide-y divide-zinc-100/80 border-t border-zinc-100/80">
          {projects.map((project) => (
            <Link key={project.id} href={`/projects/${project.id}`} className="block py-6 group hover:bg-zinc-50/50 transition-colors -mx-4 px-4 rounded-xl">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-5">
                  <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-transform group-hover:scale-105" 
                       style={{ backgroundColor: project.color ? `${project.color}15` : 'rgba(99, 102, 241, 0.08)' }}>
                    <FolderOpen className="w-5 h-5" style={{ color: project.color || '#4f46e5' }} />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-zinc-900 group-hover:text-indigo-600 transition-colors">{project.name}</h3>
                    <p className="text-zinc-500 text-sm mt-0.5 line-clamp-1 max-w-lg">
                      {project.description || "No description provided."}
                    </p>
                  </div>
                </div>
                <div className="text-xs font-medium text-zinc-400">
                  {formatDistanceToNow(new Date(project.created_at), { addSuffix: true })}
                </div>
              </div>
            </Link>
          ))}
          
          {projects.length === 0 && (
            <div className="py-16 text-center text-zinc-400 text-sm">
              No projects found. Create one to start capturing memories.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
