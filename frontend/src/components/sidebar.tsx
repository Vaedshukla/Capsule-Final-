"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  FolderOpen, 
  Search, 
  BrainCircuit, 
  ActivitySquare 
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Saved Chats", href: "/projects", icon: FolderOpen },
  { name: "Memory Explorer", href: "/explorer", icon: Search },
  { name: "Advanced Search", href: "/playground", icon: BrainCircuit },
  { name: "Settings", href: "/analytics", icon: ActivitySquare },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="w-[260px] bg-zinc-50/50 backdrop-blur-md flex flex-col h-full shrink-0">
      <div className="h-16 flex items-center px-6 mt-2">
        <div className="w-7 h-7 rounded-md bg-gradient-to-br from-zinc-800 to-zinc-950 flex items-center justify-center mr-3 shadow-sm">
          <BrainCircuit className="w-4 h-4 text-white" />
        </div>
        <span className="font-semibold text-sm text-zinc-900 tracking-tight">Project Capsule</span>
      </div>

      <nav className="flex-1 px-4 py-4 space-y-0.5 overflow-y-auto">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400 mb-2 px-2">Main Menu</div>
        {navigation.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 group relative",
                isActive
                  ? "text-zinc-900 bg-white shadow-sm border border-zinc-200/50"
                  : "text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100/50 border border-transparent"
              )}
            >
              <item.icon className={cn(
                "w-4 h-4 transition-colors",
                isActive ? "text-zinc-900" : "text-zinc-400 group-hover:text-zinc-600"
              )} strokeWidth={isActive ? 2.5 : 2} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-4">
        <div className="px-4 py-3 rounded-xl bg-white shadow-sm border border-zinc-200/50 flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)] animate-pulse" />
          <div className="flex flex-col">
            <span className="text-xs font-semibold text-zinc-800">Capsule Core</span>
            <span className="text-[10px] text-zinc-500 font-medium">Connected</span>
          </div>
        </div>
      </div>
    </div>
  );
}
