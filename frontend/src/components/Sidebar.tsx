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
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">
          <div className="logo-icon">BS</div>
          <div>
            <div className="logo-text">BlueScholar</div>
            <div className="logo-sub">
              {role === "faculty" ? "Faculty Intelligence" : "Academic Intelligence"}
            </div>
          </div>
        </div>
      </div>

      <nav style={{ flex: 1, overflowY: "auto", padding: "12px 16px" }}>
        {nav.map((section) => (
          <div key={section.section} className="nav-section">
            <div className="nav-section-label">
              {section.section}
            </div>
            <div>
              {section.links.map((link) => {
                const isActive = pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={cn("nav-item", isActive && "active")}
                  >
                    <div className="nav-icon">
                      <link.icon size={16} />
                    </div>
                    {link.label}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <button onClick={handleSignOut} className="sidebar-user nav-item">
        <div className="user-avatar" style={{ background: "rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.7)" }}>
          <LogOut size={14} />
        </div>
        <div className="user-info">
          <div className="user-name">Sign Out</div>
          <div className="user-role">Log out of account</div>
        </div>
      </button>
    </aside>
  );
}

