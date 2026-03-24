"use client";

import PageShell from "@/components/layout/PageShell";
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

export default function FacultyDashboard() {
  const stats = [
    { label: "Total Students", value: "142", sub: "+12 this intake", icon: Users, color: "var(--blue)", bg: "rgba(30, 111, 217, 0.15)", modifier: "blue" },
    { label: "Batch Readiness", value: "74%", sub: "-2% vs last week", icon: Zap, color: "var(--warning)", bg: "rgba(217, 119, 6, 0.15)", modifier: "gold" },
    { label: "Pending Reviews", value: "18", sub: "Avg time: 4.2h", icon: ClipboardList, color: "var(--danger)", bg: "rgba(220, 38, 38, 0.15)", modifier: "danger" },
    { label: "Integrity Score", value: "98%", sub: "Plagiarism verified", icon: ShieldCheck, color: "var(--success)", bg: "rgba(5, 150, 105, 0.15)", modifier: "success" },
  ];

  return (
    <PageShell
      title="Faculty Intelligence"
      subtitle="Overview of CS-101: Introduction to Computer Science"
      actions={
        <div style={{ display: "flex", gap: "12px" }}>
          <Button variant="outline" className="btn btn-secondary">
            Export Analytics
          </Button>
          <Button className="btn btn-primary">
            <Plus className="w-4 h-4" />
            Add Course Content
          </Button>
        </div>
      }
    >
      <div className="grid-4" style={{ marginBottom: "24px" }}>
        {/* Institutional Overview - Wide */}
        <div style={{ gridColumn: "span 3" }} className="card">
          <div style={{ display: "flex", flexDirection: "column", height: "100%", justifyContent: "center" }}>
            <h1 style={{ fontSize: "32px", fontWeight: "bold", lineHeight: 1.2, margin: 0 }}>
              Batch Performance <br />
              <span style={{ color: "var(--blueLight)", fontSize: "28px" }}>Critical Gaps Detected in Unit 3</span>
            </h1>
            <p style={{ marginTop: "16px", color: "var(--slateLight)", fontSize: "16px", maxWidth: "600px" }}>
              42% of students are struggling with Big O complexity after the recent lecture.
            </p>
            <div style={{ display: "flex", gap: "16px", marginTop: "24px", paddingTop: "24px" }}>
              <Button className="btn btn-primary" style={{ padding: "12px 24px" }}>
                Review Gap Report
                <ArrowRight className="w-4 h-4" style={{ marginLeft: "8px" }} />
              </Button>
              <Button style={{ background: "rgba(255,255,255,0.05)", color: "white", padding: "12px 24px", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.1)", cursor: "pointer", fontWeight: "bold" }}>
                Automate Remediation
              </Button>
            </div>
          </div>
        </div>

        {/* Content Processing Status */}
        <div className="card" style={{ display: "flex", flexDirection: "column", height: "100%" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "24px" }}>
            <div style={{ width: "40px", height: "40px", borderRadius: "8px", background: "var(--blue)", display: "flex", alignItems: "center", justifyContent: "center", color: "white" }}>
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <p style={{ fontSize: "14px", fontWeight: "bold", margin: 0 }}>Content Engine</p>
              <p style={{ fontSize: "10px", color: "var(--blueLight)", textTransform: "uppercase", letterSpacing: "1px", margin: 0 }}>ChaosCleaner Live</p>
            </div>
          </div>
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ padding: "12px", background: "rgba(255,255,255,0.05)", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.1)" }}>
              <p style={{ fontSize: "12px", fontWeight: "bold", margin: "0 0 8px" }}>Syllabus Mapping</p>
              <div style={{ width: "100%", background: "rgba(255,255,255,0.1)", height: "6px", borderRadius: "99px" }}>
                <div style={{ background: "var(--blue)", height: "100%", width: "85%", borderRadius: "99px" }} />
              </div>
            </div>
            <div style={{ padding: "12px", background: "rgba(255,255,255,0.05)", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.1)" }}>
              <p style={{ fontSize: "12px", fontWeight: "bold", margin: "0 0 8px" }}>Doc Processing</p>
              <div style={{ width: "100%", background: "rgba(255,255,255,0.1)", height: "6px", borderRadius: "99px" }}>
                <div style={{ background: "var(--blue)", height: "100%", width: "45%", borderRadius: "99px" }} />
              </div>
            </div>
          </div>
          <p style={{ marginTop: "16px", fontSize: "10px", color: "var(--blueLight)", fontWeight: "bold", textTransform: "uppercase", letterSpacing: "1px" }}>3 files in queue</p>
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
        {/* Student Performance Grid */}
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
            <h2 className="card-title" style={{ margin: 0, fontSize: "20px" }}>Batch Insight</h2>
            <span style={{ fontSize: "11px", fontWeight: "bold", background: "rgba(255,255,255,0.1)", padding: "4px 8px", borderRadius: "6px", color: "var(--slateLight)" }}>LIVE FEED</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px", background: "rgba(5, 150, 105, 0.1)", borderRadius: "12px", border: "1px solid rgba(5, 150, 105, 0.2)", cursor: "pointer" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                <div style={{ width: "48px", height: "48px", borderRadius: "12px", background: "var(--success)", display: "flex", alignItems: "center", justifyContent: "center", color: "white" }}>
                  <TrendingUp className="w-6 h-6" />
                </div>
                <div>
                  <p style={{ fontSize: "14px", fontWeight: "bold", color: "var(--success)", margin: "0 0 4px" }}>Sorting Algorithms</p>
                  <p style={{ fontSize: "12px", color: "var(--success)", opacity: 0.8, margin: 0 }}>88% Mastering this concept</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5" style={{ color: "var(--success)" }} />
            </div>

            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px", background: "rgba(220, 38, 38, 0.1)", borderRadius: "12px", border: "1px solid rgba(220, 38, 38, 0.2)", cursor: "pointer" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                <div style={{ width: "48px", height: "48px", borderRadius: "12px", background: "var(--danger)", display: "flex", alignItems: "center", justifyContent: "center", color: "white" }}>
                  <TrendingDown className="w-6 h-6" />
                </div>
                <div>
                  <p style={{ fontSize: "14px", fontWeight: "bold", color: "var(--danger)", margin: "0 0 4px" }}>Big O Complexity</p>
                  <p style={{ fontSize: "12px", color: "var(--danger)", opacity: 0.8, margin: 0 }}>42% Struggling with patterns</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5" style={{ color: "var(--danger)" }} />
            </div>
          </div>
        </div>

        {/* Recent Activity Log */}
        <div className="card">
          <div style={{ marginBottom: "24px" }}>
            <h2 className="card-title" style={{ margin: 0, fontSize: "20px" }}>Activity Intelligence</h2>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {[
              { doc: "midterm_exam_2024.pdf", action: "Plagiarism analysis finished", time: "2m ago", status: "Secure", icon: ShieldCheck, color: "var(--success)", bg: "rgba(5, 150, 105, 0.15)" },
              { doc: "unit3_slides.pptx", action: "Concept mapping completed", time: "15m ago", status: "Mapped", icon: TrendingUp, color: "var(--blue)", bg: "rgba(30, 111, 217, 0.15)" },
              { doc: "student_submission_12.zip", action: "Code calibration flagged", time: "1h ago", status: "Review", icon: AlertCircle, color: "var(--warning)", bg: "rgba(217, 119, 6, 0.15)" },
            ].map((log, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 0" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                  <div style={{ width: "40px", height: "40px", borderRadius: "12px", background: log.bg, color: log.color, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <log.icon className="w-5 h-5" />
                  </div>
                  <div>
                    <p style={{ fontSize: "14px", fontWeight: "bold", color: "white", margin: "0 0 4px", maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{log.doc}</p>
                    <p style={{ fontSize: "10px", color: "var(--slateLight)", fontWeight: "bold", textTransform: "uppercase", letterSpacing: "1px", margin: 0 }}>{log.action}</p>
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <span style={{ fontSize: "10px", fontWeight: "bold", background: "rgba(255,255,255,0.1)", padding: "4px 8px", borderRadius: "6px", color: "var(--slateLight)", display: "inline-block", marginBottom: "4px" }}>{log.status}</span>
                  <p style={{ fontSize: "11px", color: "rgba(255,255,255,0.4)", fontWeight: "bold", margin: 0 }}>{log.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </PageShell>
  );
}
