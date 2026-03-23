"use client";

import { Search, Bell, User } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { signOut } from "@/lib/supabase/auth-helpers";
import { useRouter } from "next/navigation";

export default function TopBar() {
  const router = useRouter();

  async function handleSignOut() {
    await signOut();
    router.push("/login");
  }

  return (
    <header className="h-20 border-b border-[var(--border)] bg-white sticky top-0 z-40 flex items-center justify-between px-10">
      <div className="flex-1 max-w-xl">
        <div className="relative group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
          <Input
            placeholder="Search Intelligence..."
            className="pl-12 h-11 bg-gray-50 border-transparent focus:bg-white focus:ring-2 focus:ring-blue-100 rounded-2xl transition-all"
          />
        </div>
      </div>

      <div className="flex items-center gap-6">
        <button className="p-2.5 text-gray-500 hover:bg-gray-50 rounded-2xl transition-all relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-3 right-3 w-2 h-2 bg-blue-600 rounded-full border-2 border-white"></span>
        </button>

        <div className="h-8 w-px bg-gray-100 mx-2" />

        <DropdownMenu>
          <DropdownMenuTrigger className="flex items-center gap-3 p-1.5 pl-3 hover:bg-gray-50 rounded-2xl transition-all border border-gray-100 group">
            <span className="text-sm font-semibold text-gray-900">Alex J.</span>
            <div className="w-9 h-9 rounded-xl bg-gray-900 text-white flex items-center justify-center font-bold text-xs ring-4 ring-gray-50 group-hover:ring-blue-50 transition-all">
              AJ
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64 p-2 rounded-2xl border-gray-100 shadow-xl shadow-gray-200/50">
            <DropdownMenuLabel className="px-3 py-2 text-xs font-bold text-gray-400 uppercase tracking-widest">Navigation</DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-gray-50" />
            <DropdownMenuItem onClick={() => router.push("/profile")} className="rounded-xl py-2.5 px-3">
              Profile Settings
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push("/institution")} className="rounded-xl py-2.5 px-3">
              Institutional ID
            </DropdownMenuItem>
            <DropdownMenuSeparator className="bg-gray-50" />
            <DropdownMenuItem
              onClick={handleSignOut}
              className="rounded-xl py-2.5 px-3 text-red-600 focus:text-red-700 focus:bg-red-50"
            >
              Sign Out Securely
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
