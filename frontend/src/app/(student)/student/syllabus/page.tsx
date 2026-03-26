"use client";

import { useState, useEffect } from "react";
import PageShell from "@/components/layout/PageShell";
import {
  Map,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  MinusCircle,
  BookOpen,
  MessageSquare,
  FileText,
} from "lucide-react";

interface SyllabusTopic {
  name: string;
  subtopics: string[];
  prerequisite_topics: string[];
}

interface SyllabusUnit {
  unit_number: number;
  title: string;
  weightage_marks: number;
  topics: SyllabusTopic[];
}

interface CoverageInfo {
  status: "covered" | "partial" | "gap";
  unit?: number;
  match_count: number;
  top_score?: number;
}

export default function SyllabusPage() {
  const [units, setUnits] = useState<SyllabusUnit[]>([]);
  const [coverage, setCoverage] = useState<Record<string, CoverageInfo>>({});
  const [expandedUnits, setExpandedUnits] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    const apiUrl =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
      const [syllabusRes, coverageRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/student/syllabus`),
        fetch(`${apiUrl}/api/v1/student/coverage`),
      ]);

      if (syllabusRes.ok) {
        const syllabusData = await syllabusRes.json();
        if (syllabusData?.units) {
          setUnits(syllabusData.units);
          // Expand first unit by default
          if (syllabusData.units.length > 0) {
            setExpandedUnits(new Set([syllabusData.units[0].unit_number]));
          }
        }
      }

      if (coverageRes.ok) {
        const coverageData = await coverageRes.json();
        if (coverageData?.coverage) {
          setCoverage(coverageData.coverage);
        }
      }
    } catch {
      setError("Could not load syllabus data. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  function toggleUnit(unitNum: number) {
    setExpandedUnits((prev) => {
      const next = new Set(prev);
      if (next.has(unitNum)) {
        next.delete(unitNum);
      } else {
        next.add(unitNum);
      }
      return next;
    });
  }

  function getCoverageStats() {
    const entries = Object.values(coverage);
    if (entries.length === 0) return { covered: 0, partial: 0, gap: 0, total: 0 };
    return {
      covered: entries.filter((c) => c.status === "covered").length,
      partial: entries.filter((c) => c.status === "partial").length,
      gap: entries.filter((c) => c.status === "gap").length,
      total: entries.length,
    };
  }

  function getCoverageIcon(status: string) {
    switch (status) {
      case "covered":
        return <CheckCircle2 size={14} style={{ color: "var(--success)" }} />;
      case "partial":
        return <AlertCircle size={14} style={{ color: "var(--gold)" }} />;
      case "gap":
        return <MinusCircle size={14} style={{ color: "var(--danger)" }} />;
      default:
        return <MinusCircle size={14} style={{ color: "var(--slateLight)" }} />;
    }
  }

  function getCoverageBadgeClass(status: string) {
    switch (status) {
      case "covered":
        return "badge-green";
      case "partial":
        return "badge-amber";
      case "gap":
        return "badge-red";
      default:
        return "badge-slate";
    }
  }

  const stats = getCoverageStats();

  return (
    <PageShell
      title="Syllabus Map"
      subtitle="Your syllabus structure with note coverage analysis"
      actions={
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            className="btn btn-secondary"
            style={{ fontSize: "12px" }}
            onClick={() => {
              if (expandedUnits.size === units.length) {
                setExpandedUnits(new Set());
              } else {
                setExpandedUnits(new Set(units.map((u) => u.unit_number)));
              }
            }}
          >
            {expandedUnits.size === units.length ? "Collapse All" : "Expand All"}
          </button>
        </div>
      }
    >
      {loading ? (
        <div className="card" style={{ textAlign: "center", padding: "60px" }}>
          <div className="loading-dots" style={{ justifyContent: "center" }}>
            <div className="loading-dot" />
            <div className="loading-dot" />
            <div className="loading-dot" />
          </div>
          <p style={{ marginTop: "16px", color: "var(--slateLight)" }}>
            Loading syllabus...
          </p>
        </div>
      ) : error ? (
        <div className="card" style={{ textAlign: "center", padding: "40px" }}>
          <AlertCircle
            size={28}
            style={{ color: "var(--danger)", marginBottom: "12px" }}
          />
          <p style={{ color: "var(--danger)" }}>{error}</p>
        </div>
      ) : units.length === 0 ? (
        <div
          className="card"
          style={{ textAlign: "center", padding: "60px", color: "var(--slateLight)" }}
        >
          <Map size={32} style={{ marginBottom: "12px", opacity: 0.4 }} />
          <h3 style={{ color: "white", marginBottom: "8px" }}>No syllabus found</h3>
          <p style={{ fontSize: "13px" }}>
            Upload a syllabus PDF in the Library to generate your syllabus map.
          </p>
        </div>
      ) : (
        <>
          {/* Coverage Stats */}
          {stats.total > 0 && (
            <div className="grid-4" style={{ marginBottom: "24px" }}>
              <div className="stat-card success">
                <p className="stat-label">Covered</p>
                <h2 className="stat-value">{stats.covered}</h2>
                <p style={{ fontSize: "12px", color: "var(--slateLight)" }}>
                  topics with notes
                </p>
              </div>
              <div className="stat-card gold">
                <p className="stat-label">Partial</p>
                <h2 className="stat-value">{stats.partial}</h2>
                <p style={{ fontSize: "12px", color: "var(--slateLight)" }}>
                  thin coverage
                </p>
              </div>
              <div className="stat-card" style={{ borderTopColor: "var(--danger)" }}>
                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    right: 0,
                    height: "3px",
                    background: "var(--danger)",
                    borderRadius: "12px 12px 0 0",
                  }}
                />
                <p className="stat-label">Gaps</p>
                <h2 className="stat-value">{stats.gap}</h2>
                <p style={{ fontSize: "12px", color: "var(--slateLight)" }}>
                  not in your notes
                </p>
              </div>
              <div className="stat-card blue">
                <p className="stat-label">Total Topics</p>
                <h2 className="stat-value">{stats.total}</h2>
                <p style={{ fontSize: "12px", color: "var(--slateLight)" }}>
                  in syllabus
                </p>
              </div>
            </div>
          )}

          {/* Syllabus Units */}
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {units.map((unit) => {
              const isExpanded = expandedUnits.has(unit.unit_number);
              const unitCoverage = unit.topics.map(
                (t) => coverage[t.name]?.status || "unknown"
              );
              const coveredCount = unitCoverage.filter(
                (s) => s === "covered"
              ).length;
              const coveragePct =
                unit.topics.length > 0
                  ? Math.round((coveredCount / unit.topics.length) * 100)
                  : 0;

              return (
                <div key={unit.unit_number} className="card" style={{ padding: 0 }}>
                  {/* Unit Header */}
                  <button
                    className="syllabus-unit-header"
                    onClick={() => toggleUnit(unit.unit_number)}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "12px", flex: 1 }}>
                      <div className="syllabus-unit-num">
                        U{unit.unit_number}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 600, color: "white", fontSize: "14px" }}>
                          {unit.title || `Unit ${unit.unit_number}`}
                        </div>
                        <div
                          style={{
                            fontSize: "12px",
                            color: "var(--slateLight)",
                            marginTop: "2px",
                          }}
                        >
                          {unit.topics.length} topics ·{" "}
                          {unit.weightage_marks} marks
                        </div>
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                      {/* Coverage bar */}
                      <div style={{ width: "100px" }}>
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            fontSize: "10px",
                            marginBottom: "4px",
                          }}
                        >
                          <span style={{ color: "var(--slateLight)" }}>
                            Coverage
                          </span>
                          <span style={{ color: "white", fontWeight: 600 }}>
                            {coveragePct}%
                          </span>
                        </div>
                        <div className="progress-bar-bg">
                          <div
                            className="progress-bar-fill"
                            style={{
                              width: `${coveragePct}%`,
                              background:
                                coveragePct >= 75
                                  ? "var(--success)"
                                  : coveragePct >= 40
                                    ? "var(--gold)"
                                    : "var(--danger)",
                            }}
                          />
                        </div>
                      </div>

                      <span
                        className="badge badge-blue"
                        style={{ fontSize: "10px" }}
                      >
                        {unit.weightage_marks}m
                      </span>

                      {isExpanded ? (
                        <ChevronDown size={16} style={{ color: "var(--slateLight)" }} />
                      ) : (
                        <ChevronRight size={16} style={{ color: "var(--slateLight)" }} />
                      )}
                    </div>
                  </button>

                  {/* Topics */}
                  {isExpanded && (
                    <div className="syllabus-topics">
                      {unit.topics.map((topic, ti) => {
                        const cov = coverage[topic.name];
                        const status = cov?.status || "unknown";

                        return (
                          <div key={ti} className="syllabus-topic">
                            <div
                              style={{
                                display: "flex",
                                alignItems: "flex-start",
                                gap: "10px",
                                flex: 1,
                              }}
                            >
                              {getCoverageIcon(status)}
                              <div style={{ flex: 1 }}>
                                <div
                                  style={{
                                    fontSize: "13px",
                                    fontWeight: 500,
                                    color: "white",
                                  }}
                                >
                                  {topic.name}
                                </div>
                                {topic.subtopics.length > 0 && (
                                  <div
                                    style={{
                                      fontSize: "11px",
                                      color: "var(--slateLight)",
                                      marginTop: "4px",
                                      lineHeight: 1.5,
                                    }}
                                  >
                                    {topic.subtopics.join(" · ")}
                                  </div>
                                )}
                                {topic.prerequisite_topics.length > 0 && (
                                  <div
                                    style={{
                                      fontSize: "10px",
                                      color: "var(--gold)",
                                      marginTop: "4px",
                                    }}
                                  >
                                    Prereq: {topic.prerequisite_topics.join(", ")}
                                  </div>
                                )}
                              </div>
                            </div>

                            <div
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "8px",
                              }}
                            >
                              <span
                                className={`badge ${getCoverageBadgeClass(status)}`}
                                style={{ fontSize: "10px" }}
                              >
                                {status === "covered"
                                  ? "Covered"
                                  : status === "partial"
                                    ? "Partial"
                                    : status === "gap"
                                      ? "Gap"
                                      : "Unknown"}
                              </span>
                              <a
                                href={`/student/doubt?q=Explain ${encodeURIComponent(topic.name)}`}
                                style={{
                                  color: "var(--blue)",
                                  cursor: "pointer",
                                  display: "flex",
                                  alignItems: "center",
                                }}
                                title="Ask DocDoubt about this topic"
                              >
                                <MessageSquare size={14} />
                              </a>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </PageShell>
  );
}
