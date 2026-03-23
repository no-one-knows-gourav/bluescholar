"use client";

import PageShell from "@/components/layout/PageShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Plus,
  BookOpen,
  CheckCircle2,
  Clock,
  ArrowRight,
  TrendingUp,
  Brain,
  Timer,
  FileText,
  Sparkles,
  ChevronRight
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export default function StudentDashboard() {
  const stats = [
    { label: "Syllabus Coverage", value: "68%", sub: "+12.4% this week", icon: BookOpen, color: "text-blue-600", bg: "bg-blue-50" },
    { label: "AI Readiness Score", value: "B+", sub: "Verified for Midterms", icon: Brain, color: "text-purple-600", bg: "bg-purple-50" },
    { label: "Docs Processed", value: "24", sub: "182 pages analyzed", icon: FileText, color: "text-emerald-600", bg: "bg-emerald-50" },
    { label: "Active Streak", value: "5 Days", sub: "Personal Best: 12", icon: Sparkles, color: "text-amber-600", bg: "bg-amber-50" },
  ];

  return (
    <PageShell
      title="Dashboard"
      subtitle="Welcome back, Alex. Your learning engine is primed."
      actions={
        <div className="flex gap-3">
          <Button variant="outline" className="rounded-2xl h-11 px-6 font-semibold border-gray-200">
            View Analytics
          </Button>
          <Button className="rounded-2xl h-11 px-6 font-semibold bg-black hover:bg-gray-900 text-white gap-2">
            <Plus className="w-4 h-4" />
            Upload Document
          </Button>
        </div>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 auto-rows-min">
        {/* Welcome Block - Full Width */}
        <div className="lg:col-span-3 bg-blue-600 rounded-3xl p-10 flex flex-col justify-between text-white relative overflow-hidden group">
          <div className="relative z-10 max-w-lg">
            <h1 className="text-4xl font-display font-bold leading-tight">
              Ready to crush Unit 3? <br />
              <span className="text-blue-200">Neural Networks are waiting.</span>
            </h1>
            <p className="mt-4 text-blue-100 text-lg font-medium opacity-90">
              Your overall readiness is B+. Complete today&apos;s 2 practice sets to hit A-.
            </p>
            <Button className="mt-8 bg-white text-blue-600 hover:bg-blue-50 rounded-2xl h-12 px-8 font-bold gap-2 group">
              Start Session
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Button>
          </div>
          <div className="absolute right-[-5%] bottom-[-10%] opacity-10 group-hover:scale-110 transition-transform duration-700">
            <Sparkles className="w-64 h-64 text-white" />
          </div>
        </div>

        {/* AI Quick Assistant */}
        <Card className="rounded-3xl border-none bg-gray-950 text-white shadow-2xl p-2 h-full">
          <CardContent className="p-6 h-full flex flex-col">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center">
                <Brain className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-bold">Scholar Chat</p>
                <p className="text-[10px] text-white/40 uppercase tracking-widest">Active Intelligence</p>
              </div>
            </div>
            <div className="flex-1 bg-white/5 rounded-2xl p-4 text-xs text-white/70 leading-relaxed italic">
              &quot;I noticed you struggled with Backpropagation. Should we generate a 5-minute summary?&quot;
            </div>
            <div className="mt-4 flex gap-2">
              <input
                placeholder="Ask anything..."
                className="bg-white/5 border-none rounded-xl px-4 py-2.5 text-xs text-white flex-1 focus:ring-1 focus:ring-blue-500 transition-all outline-none"
              />
              <Button size="icon" className="bg-blue-600 hover:bg-blue-700 rounded-xl">
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
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

        {/* Pulse Chart Placeholder */}
        <Card className="lg:col-span-2 rounded-3xl border-gray-100 bg-white p-8">
          <CardHeader className="p-0 mb-6 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-xl font-display font-bold">Intelligence Pulse</CardTitle>
              <p className="text-xs text-gray-400 mt-1 uppercase tracking-widest font-bold">Learning consistency last 14 days</p>
            </div>
            <Badge className="bg-blue-50 text-blue-600 border-none rounded-lg px-3 py-1 font-bold">+24%</Badge>
          </CardHeader>
          <div className="h-48 w-full bg-gray-50 rounded-2xl flex items-end px-4 py-6 gap-2">
            {[40, 60, 45, 90, 65, 80, 50, 70, 85, 95, 60, 75].map((h, i) => (
              <div key={i} className="flex-1 bg-blue-100 hover:bg-blue-600 rounded-t-lg transition-all" style={{ height: `${h}%` }} />
            ))}
          </div>
        </Card>

        {/* Focus Timer */}
        <Card className="rounded-3xl border-none bg-blue-50 p-8 flex flex-col justify-between overflow-hidden relative">
          <div className="relative z-10">
            <Badge className="bg-blue-200 text-blue-800 border-none mb-4 px-3 py-1 font-bold">FOCUS MODE</Badge>
            <h3 className="text-2xl font-display font-bold text-blue-900 leading-tight">Deep Work <br />Session</h3>
          </div>
          <div className="relative z-10 flex items-center justify-between mt-8">
            <div className="text-3xl font-mono font-bold text-blue-600 tracking-tighter">25:00</div>
            <Button size="icon" className="bg-blue-600 text-white rounded-2xl h-12 w-12 hover:scale-110 transition-transform">
              <Timer className="w-6 h-6" />
            </Button>
          </div>
          <Sparkles className="absolute right-[-10%] top-[-10%] w-32 h-32 text-blue-100 opacity-50" />
        </Card>

        {/* Resource Feed */}
        <Card className="rounded-3xl border-gray-100 bg-white p-8">
          <CardHeader className="p-0 mb-6 flex flex-row items-center justify-between">
            <CardTitle className="text-xl font-display font-bold">Recent Intelligence</CardTitle>
            <Button variant="ghost" size="sm" className="text-blue-600 font-bold hover:bg-blue-50">See All</Button>
          </CardHeader>
          <div className="space-y-4">
            {[
              { name: "Unit 3 Flashcards", type: "Generated", icon: Brain, color: "text-purple-600" },
              { name: "Algorithms Summary", type: "PDF Parse", icon: FileText, color: "text-emerald-600" },
              { name: "Mock Test #4 Results", type: "Review", icon: CheckCircle2, color: "text-blue-600" },
            ].map((feed, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-2xl hover:bg-gray-50 transition-colors cursor-pointer group">
                <div className="flex items-center gap-3">
                  <div className={cn("w-10 h-10 rounded-xl bg-gray-50 flex items-center justify-center group-hover:scale-110 transition-transform", feed.color)}>
                    <feed.icon className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-bold">{feed.name}</p>
                    <p className="text-[10px] text-gray-400 font-medium">{feed.type}</p>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-blue-600 transition-colors" />
              </div>
            ))}
          </div>
        </Card>
      </div>
    </PageShell>
  );
}
