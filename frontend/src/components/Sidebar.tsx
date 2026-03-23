"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Library,
  Map,
  MessageSquare,
  Brain,
  FileSearch,
  Search,
  Clock,
  Microscope,
  BookOpen,
  Users,
  ClipboardList,
  PenTool,
  SearchCode,
  TrendingDown,
  Scale,
  FileText,
  LogOut
} from "lucide-react";

const studentNav = [
  {
    section: "Overview",
    links: [
      { href: "/student/dashboard", label: "Dashboard", icon: LayoutDashboard },
    ],
  },
  {
    section: "Prepare",
    links: [
      { href: "/student/library", label: "Library", icon: Library },
      { href: "/student/syllabus", label: "Syllabus Map", icon: Map },
      { href: "/student/doubt", label: "DocDoubt", icon: MessageSquare },
      { href: "/student/tutor", label: "MemoryTutor", icon: Brain },
    ],
  },
  {
    section: "Practice",
    links: [
      { href: "/student/mock", label: "Smart Mock", icon: ClipboardList },
      { href: "/student/patterns", label: "Pattern Miner", icon: FileSearch },
      { href: "/student/planner", label: "Revision Clock", icon: Clock },
    ],
  },
  {
    section: "Research",
    links: [
      { href: "/student/researcher", label: "AutoResearcher", icon: Microscope },
    ],
  },
];

const facultyNav = [
  {
    section: "Overview",
    links: [
      { href: "/faculty/dashboard", label: "Dashboard", icon: LayoutDashboard },
    ],
  },
  {
    section: "Content",
    links: [
      { href: "/faculty/courseware", label: "Courseware", icon: BookOpen },
      { href: "/faculty/students", label: "Students", icon: Users },
    ],
  },
  {
    section: "Assessment",
    links: [
      { href: "/faculty/exams", label: "Exams", icon: ClipboardList },
      { href: "/faculty/grading", label: "Grading", icon: PenTool },
      { href: "/faculty/plagiarism", label: "PlagueScope", icon: SearchCode },
    ],
  },
  {
    section: "Analytics",
    links: [
      { href: "/faculty/gaps", label: "Gap Finder", icon: TrendingDown },
      { href: "/faculty/calibrator", label: "Calibrator", icon: Scale },
      { href: "/faculty/reports", label: "Reports", icon: FileText },
    ],
  },
];

interface SidebarProps {
  role: "student" | "faculty";
}

export default function Sidebar({ role }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const nav = role === "faculty" ? facultyNav : studentNav;

  async function handleSignOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
  }

  return (
    <aside className="sidebar bg-[#010101] border-r border-white/5 flex flex-col h-screen sticky top-0">
      <div className="p-10 mb-4">
        <h2 className="text-2xl font-display font-bold text-white tracking-tight">
          Blue<span className="text-blue-500">Scholar</span>
        </h2>
        <p className="text-[10px] uppercase tracking-widest text-white/40 mt-1 font-medium italic">
          {role === "faculty" ? "Faculty Intelligence" : "Academic Intelligence"}
        </p>
      </div>

      <nav className="flex-1 px-6 space-y-10 overflow-y-auto overflow-x-hidden pb-10">
        {nav.map((section) => (
          <div key={section.section} className="space-y-4">
            <div className="px-4 text-[10px] font-bold uppercase tracking-widest text-white/20">
              {section.section}
            </div>
            <div className="space-y-2">
              {section.links.map((link) => {
                const isActive = pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={cn(
                      "flex items-center gap-4 px-5 py-3 rounded-xl text-sm font-medium transition-all duration-200 group",
                      isActive
                        ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                        : "text-white/50 hover:text-white hover:bg-white/5"
                    )}
                  >
                    <link.icon className={cn(
                      "w-4 h-4 transition-transform duration-200",
                      isActive ? "scale-110" : "group-hover:scale-110"
                    )} />
                    {link.label}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="p-4 mt-auto border-t border-white/5">
        <button
          onClick={handleSignOut}
          className="flex items-center gap-3 w-full px-4 py-2.5 rounded-xl text-sm font-medium text-white/50 hover:text-white hover:bg-white/5 transition-all duration-200"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
