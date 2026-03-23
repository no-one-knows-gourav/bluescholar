import Link from "next/link";

export default function Home() {
  return (
    <div className="auth-container" style={{ flexDirection: "column", gap: "2rem" }}>
      <div style={{ textAlign: "center", maxWidth: 600 }}>
        <h1 style={{ fontSize: "3rem", marginBottom: "1rem" }}>
          <span className="text-gradient">BlueScholar</span>
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "1.125rem", lineHeight: 1.6 }}>
          AI-powered academic preparation and evaluation platform for students and faculty.
          Upload your notes, parse syllabi, practice with smart mocks, and track your readiness.
        </p>
      </div>

      <div style={{ display: "flex", gap: "1rem" }}>
        <Link href="/login" className="btn btn-primary" style={{ padding: "0.75rem 2rem", fontSize: "1rem" }}>
          Sign In
        </Link>
        <Link href="/register" className="btn btn-secondary" style={{ padding: "0.75rem 2rem", fontSize: "1rem" }}>
          Create Account
        </Link>
      </div>

      <div className="stats-grid" style={{ maxWidth: 800, width: "100%", marginTop: "2rem" }}>
        <div className="stat-card animate-fade-in" style={{ animationDelay: "0.1s" }}>
          <div className="label">Smart Engines</div>
          <div className="value" style={{ color: "var(--accent-blue)" }}>14</div>
          <div className="change" style={{ color: "var(--text-secondary)" }}>AI-powered features</div>
        </div>
        <div className="stat-card animate-fade-in" style={{ animationDelay: "0.2s" }}>
          <div className="label">Document Types</div>
          <div className="value" style={{ color: "var(--accent-green)" }}>6</div>
          <div className="change" style={{ color: "var(--text-secondary)" }}>PDF, DOCX, PPTX, TXT, Images</div>
        </div>
        <div className="stat-card animate-fade-in" style={{ animationDelay: "0.3s" }}>
          <div className="label">Coverage Analysis</div>
          <div className="value" style={{ color: "var(--accent-amber)" }}>100%</div>
          <div className="change" style={{ color: "var(--text-secondary)" }}>Syllabus mapped</div>
        </div>
      </div>
    </div>
  );
}
