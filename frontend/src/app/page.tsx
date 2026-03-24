import Link from "next/link";

export default function Home() {
  return (
    <div style={{ display: "flex", flex: 1, width: "100%", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "100vh", gap: "2rem", padding: "2rem" }}>
      <div style={{ textAlign: "center", maxWidth: 640 }}>
        <h1 className="serif" style={{ fontSize: "3.5rem", marginBottom: "1rem", color: "var(--navy)" }}>
          BlueScholar
        </h1>
        <p style={{ color: "var(--textMid)", fontSize: "1.125rem", lineHeight: 1.6 }}>
          AI-powered academic preparation and evaluation platform for students and faculty.
          Upload your notes, parse syllabi, practice with smart mocks, and track your readiness.
        </p>
      </div>

      <div style={{ display: "flex", gap: "1rem" }}>
        <Link href="/login" className="btn btn-primary" style={{ padding: "0.875rem 2rem", fontSize: "1rem" }}>
          Sign In
        </Link>
        <Link href="/register" className="btn btn-secondary" style={{ padding: "0.875rem 2rem", fontSize: "1rem" }}>
          Create Account
        </Link>
      </div>

      <div className="grid-3" style={{ maxWidth: 800, width: "100%", marginTop: "2rem" }}>
        <div className="stat-card blue">
          <div className="stat-label">Smart Engines</div>
          <div className="stat-value">14</div>
          <div className="stat-change neutral">AI-powered features</div>
        </div>
        <div className="stat-card success">
          <div className="stat-label">Document Types</div>
          <div className="stat-value">6</div>
          <div className="stat-change neutral">PDF, DOCX, PPTX, TXT, Images</div>
        </div>
        <div className="stat-card gold">
          <div className="stat-label">Coverage Analysis</div>
          <div className="stat-value">100%</div>
          <div className="stat-change neutral">Syllabus mapped</div>
        </div>
      </div>
    </div>
  );
}
