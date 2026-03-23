"use client";

import PageShell from "@/components/layout/PageShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Users,
  FileText,
  AlertCircle,
  TrendingUp,
  Plus,
  ArrowRight,
  ClipboardList,
  ShieldCheck,
  Zap,
  ChevronRight,
  TrendingDown
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function FacultyDashboard() {
  const stats = [
    { label: "Total Students", value: "142", sub: "+12 this intake", icon: Users, color: "text-blue-600", bg: "bg-blue-50" },
    { label: "Batch Readiness", value: "74%", sub: "-2% vs last week", icon: Zap, color: "text-amber-600", bg: "bg-amber-50" },
    { label: "Pending Reviews", value: "18", sub: "Avg time: 4.2h", icon: ClipboardList, color: "text-red-600", bg: "bg-red-50" },
    { label: "Integrity Score", value: "98%", sub: "Plagiarism verified", icon: ShieldCheck, color: "text-emerald-600", bg: "bg-emerald-50" },
  ];

  return (
    <PageShell
      title="Faculty Intelligence"
      subtitle="Overview of CS-101: Introduction to Computer Science"
      actions={
        <div className="flex gap-3">
          <Button variant="outline" className="rounded-2xl h-11 px-6 font-semibold border-gray-200">
            Export Analytics
          </Button>
          <Button className="rounded-2xl h-11 px-6 font-semibold bg-black hover:bg-gray-900 text-white gap-2">
            <Plus className="w-4 h-4" />
            Add Course Content
          </Button>
        </div>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 auto-rows-min">
        {/* Institutional Overview - Wide */}
        <div className="lg:col-span-3 bg-gray-900 rounded-3xl p-10 flex flex-col justify-between text-white relative overflow-hidden group">
          <div className="relative z-10 max-w-lg">
            <h1 className="text-4xl font-display font-bold leading-tight">
              Batch Performance <br />
              <span className="text-blue-500 text-3xl">Critical Gaps Detected in Unit 3</span>
            </h1>
            <p className="mt-4 text-gray-400 text-lg font-medium">
              42% of students are struggling with Big O complexity after the recent lecture.
            </p>
            <div className="flex gap-4 mt-8">
              <Button className="bg-blue-600 text-white hover:bg-blue-700 rounded-2xl h-12 px-8 font-bold gap-2 group">
                Review Gap Report
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Button>
              <Button className="bg-white/5 hover:bg-white/10 text-white border-white/10 rounded-2xl h-12 px-8 font-bold">
                Automate Remediation
              </Button>
            </div>
          </div>
          <div className="absolute right-0 bottom-0 opacity-20 pointer-events-none group-hover:scale-105 transition-transform duration-1000">
            <TrendingUp className="w-80 h-80 text-blue-500" />
          </div>
        </div>

        {/* Content Processing Status */}
        <Card className="rounded-3xl border-none bg-blue-50 text-blue-900 p-8 h-full">
          <CardContent className="p-0 h-full flex flex-col">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white">
                <Zap className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-bold">Content Engine</p>
                <p className="text-[10px] text-blue-400 uppercase tracking-widest font-bold">ChaosCleaner Live</p>
              </div>
            </div>
            <div className="flex-1 space-y-4">
              <div className="p-4 bg-white/50 rounded-2xl border border-blue-100">
                <p className="text-xs font-bold text-blue-800">Syllabus Mapping</p>
                <div className="w-full bg-blue-200 h-1.5 rounded-full mt-2 overflow-hidden">
                  <div className="bg-blue-600 h-full w-[85%]" />
                </div>
              </div>
              <div className="p-4 bg-white/50 rounded-2xl border border-blue-100">
                <p className="text-xs font-bold text-blue-800">Doc Processing</p>
                <div className="w-full bg-blue-200 h-1.5 rounded-full mt-2 overflow-hidden">
                  <div className="bg-blue-600 h-full w-[45%]" />
                </div>
              </div>
            </div>
            <p className="mt-6 text-[10px] text-blue-500 font-bold uppercase tracking-widest">3 files in queue</p>
          </CardContent>
        </Card>

        {/* Stats Row */}
        {stats.map((stat, i) => (
          <Card key={i} className="rounded-3xl border-gray-100 bg-white hover:shadow-xl hover:shadow-gray-200/50 transition-all group">
            <CardContent className="p-8">
              <div className={cn("w-12 h-12 rounded-2xl flex items-center justify-center mb-6 transition-transform group-hover:scale-110", stat.bg, stat.color)}>
                <stat.icon className="w-6 h-6" />
              </div>
              <p className="text-sm font-semibold text-gray-500">{stat.label}</p>
              <h2 className="text-3xl font-display font-bold mt-1">{stat.value}</h2>
              <p className="text-xs font-medium text-gray-400 mt-2">{stat.sub}</p>
            </CardContent>
          </Card>
        ))}

        {/* Student Performance Grid - Double width */}
        <Card className="lg:col-span-2 rounded-3xl border-gray-100 bg-white p-8">
          <CardHeader className="p-0 mb-8 flex flex-row items-center justify-between">
            <CardTitle className="text-xl font-display font-bold">Batch Insight</CardTitle>
            <Badge className="bg-gray-50 text-gray-500 border-none font-bold">LIVE FEED</Badge>
          </CardHeader>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 rounded-2xl bg-emerald-50 border border-emerald-100 group cursor-pointer hover:bg-emerald-100 transition-colors">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-white flex items-center justify-center text-emerald-600 shadow-sm transition-transform group-hover:scale-110">
                  <TrendingUp className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm font-bold text-emerald-900">Sorting Algorithms</p>
                  <p className="text-xs text-emerald-600 font-medium tracking-tight">88% Mastering this concept</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-emerald-300" />
            </div>

            <div className="flex items-center justify-between p-4 rounded-2xl bg-red-50 border border-red-100 group cursor-pointer hover:bg-red-100 transition-colors">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-white flex items-center justify-center text-red-600 shadow-sm transition-transform group-hover:scale-110">
                  <TrendingDown className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm font-bold text-red-900">Big O Complexity</p>
                  <p className="text-xs text-red-600 font-medium tracking-tight">42% Struggling with patterns</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-red-300" />
            </div>
          </div>
        </Card>

        {/* Recent Activity Log */}
        <Card className="lg:col-span-2 rounded-3xl border-gray-100 bg-white p-8 overflow-hidden relative">
          <CardHeader className="p-0 mb-6">
            <CardTitle className="text-xl font-display font-bold">Activity Intelligence</CardTitle>
          </CardHeader>
          <div className="space-y-4">
            {[
              { doc: "midterm_exam_2024.pdf", action: "Plagiarism analysis finished", time: "2m ago", status: "Secure", icon: ShieldCheck, color: "text-emerald-500" },
              { doc: "unit3_slides.pptx", action: "Concept mapping completed", time: "15m ago", status: "Mapped", icon: TrendingUp, color: "text-blue-500" },
              { doc: "student_submission_12.zip", action: "Code calibration flagged", time: "1h ago", status: "Review", icon: AlertCircle, color: "text-amber-500" },
            ].map((log, i) => (
              <div key={i} className="flex items-center justify-between py-1 group cursor-default">
                <div className="flex items-center gap-4">
                  <div className={cn("w-10 h-10 rounded-xl bg-gray-50 flex items-center justify-center", log.color)}>
                    <log.icon className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-gray-900 truncate max-w-[200px]">{log.doc}</p>
                    <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-widest">{log.action}</p>
                  </div>
                </div>
                <div className="text-right">
                  <Badge className="bg-gray-50 text-gray-600 border-none font-bold text-[10px]">{log.status}</Badge>
                  <p className="text-[10px] text-gray-300 mt-1 font-bold">{log.time}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </PageShell>
  );
}
