"use client";

import PageShell from "@/components/layout/PageShell";
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

export default function StudentDashboard() {
  const stats = [
    { label: "Syllabus Coverage", value: "68%", sub: "+12.4% this week", icon: BookOpen, color: "var(--blue)", bg: "rgba(30, 111, 217, 0.15)", modifier: "blue" },
    { label: "AI Readiness Score", value: "B+", sub: "Verified for Midterms", icon: Brain, color: "var(--teal)", bg: "rgba(13, 148, 136, 0.15)", modifier: "teal" },
    { label: "Docs Processed", value: "24", sub: "182 pages analyzed", icon: FileText, color: "var(--success)", bg: "rgba(5, 150, 105, 0.15)", modifier: "success" },
    { label: "Active Streak", value: "5 Days", sub: "Personal Best: 12", icon: Sparkles, color: "var(--gold)", bg: "rgba(217, 119, 6, 0.15)", modifier: "gold" },
  ];

  return (
    <PageShell
      title="Dashboard"
      subtitle="Welcome back, Alex. Your learning engine is primed."
      actions={
        <div style={{ display: "flex", gap: "12px" }}>
          <Button variant="outline" className="btn btn-secondary">
            View Analytics
          </Button>
          <Button className="btn btn-primary">
            <Plus className="w-4 h-4" />
            Upload Document
          </Button>
        </div>
      }
    >
      <div className="grid-4" style={{ marginBottom: "24px" }}>
        {/* Welcome Block - Full Width */}
        <div style={{ gridColumn: "span 3" }} className="card">
          <div style={{ display: "flex", flexDirection: "column", height: "100%", justifyContent: "center", position: "relative", zIndex: 10 }}>
            <h1 style={{ fontSize: "32px", fontWeight: "bold", lineHeight: 1.2, margin: 0 }}>
              Ready to crush Unit 3? <br />
              <span style={{ color: "var(--blueLight)", fontSize: "28px" }}>Neural Networks are waiting.</span>
            </h1>
            <p style={{ marginTop: "16px", color: "var(--slateLight)", fontSize: "16px", maxWidth: "600px" }}>
              Your overall readiness is B+. Complete today&apos;s 2 practice sets to hit A-.
            </p>
            <div style={{ display: "flex", gap: "16px", marginTop: "24px", paddingTop: "24px" }}>
              <Button className="btn btn-primary" style={{ padding: "12px 24px" }}>
                Start Session
                <ArrowRight className="w-4 h-4" style={{ marginLeft: "8px" }} />
              </Button>
            </div>
          </div>
        </div>

        {/* AI Quick Assistant */}
        <div className="card" style={{ display: "flex", flexDirection: "column", height: "100%", background: "var(--navy)" }}>
          <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "24px" }}>
              <div style={{ width: "40px", height: "40px", borderRadius: "8px", background: "var(--blue)", display: "flex", alignItems: "center", justifyContent: "center", color: "white" }}>
                <Brain className="w-5 h-5" />
              </div>
              <div>
                <p style={{ fontSize: "14px", fontWeight: "bold", margin: 0, color: "white" }}>Scholar Chat</p>
                <p style={{ fontSize: "10px", color: "var(--blueLight)", textTransform: "uppercase", letterSpacing: "1px", margin: 0 }}>Active Intelligence</p>
              </div>
            </div>
            <div style={{ flex: 1, background: "rgba(255,255,255,0.05)", borderRadius: "12px", padding: "16px", fontSize: "12px", color: "rgba(255,255,255,0.7)", fontStyle: "italic", lineHeight: 1.5 }}>
              &quot;I noticed you struggled with Backpropagation. Should we generate a 5-minute summary?&quot;
            </div>
            <div style={{ display: "flex", gap: "8px", marginTop: "16px" }}>
              <input
                placeholder="Ask anything..."
                style={{ flex: 1, background: "rgba(255,255,255,0.05)", border: "none", borderRadius: "8px", padding: "10px 16px", fontSize: "12px", color: "white", outline: "none", fontFamily: "inherit" }}
              />
              <Button size="icon" style={{ background: "var(--blue)", color: "white", border: "none", borderRadius: "8px", width: "40px", height: "40px", flexShrink: 0, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid-4" style={{ marginBottom: "24px" }}>
        {stats.map((stat, i) => (
          <div key={i} className={`stat-card ${stat.modifier}`}>
            <div style={{ width: "48px", height: "48px", borderRadius: "12px", background: stat.bg, color: stat.color, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "16px" }}>
              <stat.icon className="w-6 h-6" />
            </div>
            <p className="stat-label">{stat.label}</p>
            <h2 className="stat-value">{stat.value}</h2>
            <p style={{ fontSize: "12px", color: "var(--slateLight)", margin: 0 }}>{stat.sub}</p>
          </div>
        ))}
      </div>

      <div className="grid-2">
        {/* Intelligence Pulse Chart Placeholder */}
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
            <div>
              <h2 className="card-title" style={{ margin: 0, fontSize: "20px" }}>Intelligence Pulse</h2>
              <p style={{ fontSize: "10px", color: "var(--slateLight)", textTransform: "uppercase", letterSpacing: "1px", fontWeight: "bold", margin: "4px 0 0" }}>Learning consistency last 14 days</p>
            </div>
            <span style={{ fontSize: "12px", fontWeight: "bold", background: "rgba(30, 111, 217, 0.15)", padding: "4px 10px", borderRadius: "8px", color: "var(--blue)" }}>+24%</span>
          </div>
          <div style={{ height: "192px", width: "100%", background: "rgba(255,255,255,0.02)", borderRadius: "12px", display: "flex", alignItems: "flex-end", padding: "16px 16px 0", gap: "8px" }}>
            {[40, 60, 45, 90, 65, 80, 50, 70, 85, 95, 60, 75].map((h, i) => (
              <div key={i} style={{ flex: 1, background: "rgba(30, 111, 217, 0.3)", height: `${h}%`, borderRadius: "8px 8px 0 0", transition: "all 0.2s" }} />
            ))}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Focus Timer */}
          <div className="card" style={{ flex: 0, position: "relative", overflow: "hidden", background: "rgba(30, 111, 217, 0.1)" }}>
            <span style={{ background: "rgba(30, 111, 217, 0.2)", color: "var(--blue)", padding: "4px 10px", borderRadius: "6px", fontSize: "10px", fontWeight: "bold", display: "inline-block", marginBottom: "16px" }}>FOCUS MODE</span>
            <h3 style={{ fontSize: "24px", fontWeight: "bold", color: "var(--blueLight)", lineHeight: 1.2, margin: 0 }}>Deep Work <br />Session</h3>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "32px" }}>
              <div style={{ fontSize: "36px", fontFamily: "monospace", fontWeight: "bold", color: "white", letterSpacing: "-1px" }}>25:00</div>
              <Button size="icon" style={{ background: "var(--blue)", color: "white", borderRadius: "12px", height: "48px", width: "48px", border: "none" }}>
                <Timer className="w-6 h-6" />
              </Button>
            </div>
          </div>

          {/* Resource Feed */}
          <div className="card" style={{ flex: 1 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h2 className="card-title" style={{ margin: 0, fontSize: "18px" }}>Recent Intelligence</h2>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {[
                { name: "Unit 3 Flashcards", type: "Generated", icon: Brain, color: "var(--teal)", bg: "rgba(13, 148, 136, 0.1)" },
                { name: "Algorithms Summary", type: "PDF Parse", icon: FileText, color: "var(--success)", bg: "rgba(5, 150, 105, 0.1)" },
                { name: "Mock Test #4 Results", type: "Review", icon: CheckCircle2, color: "var(--blue)", bg: "rgba(30, 111, 217, 0.1)" },
              ].map((feed, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px", borderRadius: "12px", background: "rgba(255,255,255,0.03)" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <div style={{ width: "36px", height: "36px", borderRadius: "8px", background: feed.bg, color: feed.color, display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <feed.icon className="w-5 h-5" />
                    </div>
                    <div>
                      <p style={{ fontSize: "14px", fontWeight: "bold", margin: 0, color: "white" }}>{feed.name}</p>
                      <p style={{ fontSize: "10px", color: "var(--slateLight)", margin: 0 }}>{feed.type}</p>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4" style={{ color: "rgba(255,255,255,0.2)" }} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
