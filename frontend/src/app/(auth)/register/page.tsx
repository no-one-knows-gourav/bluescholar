"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    fullName: "",
    email: "",
    password: "",
    role: "student" as "student" | "faculty",
    rollNumber: "",
    enrollmentCode: "",
    institutionName: "",
    university: "",
    department: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function updateField(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const supabase = createClient();

    const { error: authError } = await supabase.auth.signUp({
      email: form.email,
      password: form.password,
      options: {
        data: {
          full_name: form.fullName,
          role: form.role,
          roll_number: form.rollNumber || undefined,
          department: form.department || undefined,
        },
      },
    });

    if (authError) {
      setError(authError.message);
      setLoading(false);
      return;
    }

    router.push("/onboarding");
  }

  return (
    <div style={{ display: "flex", flex: 1, width: "100%", alignItems: "center", justifyContent: "center", minHeight: "100vh", padding: "2rem" }}>
      <div className="card card-lg animate-fade-in" style={{ width: "100%", maxWidth: 500 }}>
        <h1 className="serif" style={{ fontSize: "2rem", marginBottom: "0.25rem", color: "var(--navy)" }}>Create Account</h1>
        <p style={{ color: "var(--textLight)", fontSize: "0.875rem", marginBottom: "1.5rem" }}>Join BlueScholar as a student or faculty</p>

        {error && (
          <div
            style={{
              background: "var(--dangerPale)",
              color: "var(--danger)",
              padding: "0.75rem 1rem",
              borderRadius: "8px",
              fontSize: "0.875rem",
              marginBottom: "1.25rem",
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {/* Role selector */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <label style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--textMid)" }}>I am a</label>
            <div style={{ display: "flex", gap: "0.75rem" }}>
              {(["student", "faculty"] as const).map((role) => (
                <button
                  key={role}
                  type="button"
                  className={`btn ${form.role === role ? "btn-primary" : "btn-secondary"}`}
                  style={{ flex: 1, textTransform: "capitalize", justifyContent: "center", padding: "0.75rem" }}
                  onClick={() => updateField("role", role)}
                >
                  {role}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <label htmlFor="fullName" style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--textMid)" }}>Full Name</label>
            <input
              id="fullName"
              type="text"
              style={{ padding: "0.75rem", borderRadius: "8px", border: "1px solid var(--border-color)", fontSize: "0.875rem", outline: "none", fontFamily: "inherit" }}
              placeholder="Your full name"
              value={form.fullName}
              onChange={(e) => updateField("fullName", e.target.value)}
              required
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <label htmlFor="reg-email" style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--textMid)" }}>Email</label>
            <input
              id="reg-email"
              type="email"
              style={{ padding: "0.75rem", borderRadius: "8px", border: "1px solid var(--border-color)", fontSize: "0.875rem", outline: "none", fontFamily: "inherit" }}
              placeholder="you@university.edu"
              value={form.email}
              onChange={(e) => updateField("email", e.target.value)}
              required
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <label htmlFor="reg-password" style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--textMid)" }}>Password</label>
            <input
              id="reg-password"
              type="password"
              style={{ padding: "0.75rem", borderRadius: "8px", border: "1px solid var(--border-color)", fontSize: "0.875rem", outline: "none", fontFamily: "inherit" }}
              placeholder="Min 8 characters"
              value={form.password}
              onChange={(e) => updateField("password", e.target.value)}
              required
              minLength={8}
            />
          </div>

          {/* Student-specific fields */}
          {form.role === "student" && (
            <>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <label htmlFor="rollNumber" style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--textMid)" }}>Roll Number</label>
                <input
                  id="rollNumber"
                  type="text"
                  style={{ padding: "0.75rem", borderRadius: "8px", border: "1px solid var(--border-color)", fontSize: "0.875rem", outline: "none", fontFamily: "inherit" }}
                  placeholder="e.g. 21CS3045"
                  value={form.rollNumber}
                  onChange={(e) => updateField("rollNumber", e.target.value)}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <label htmlFor="enrollmentCode" style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--textMid)" }}>Enrollment Code</label>
                <input
                  id="enrollmentCode"
                  type="text"
                  style={{ padding: "0.75rem", borderRadius: "8px", border: "1px solid var(--border-color)", fontSize: "0.875rem", outline: "none", fontFamily: "inherit" }}
                  placeholder="6-digit code from your faculty"
                  value={form.enrollmentCode}
                  onChange={(e) => updateField("enrollmentCode", e.target.value)}
                  maxLength={6}
                />
              </div>
            </>
          )}

          {/* Faculty-specific fields */}
          {form.role === "faculty" && (
            <>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <label htmlFor="institutionName" style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--textMid)" }}>Institution Name</label>
                <input
                  id="institutionName"
                  type="text"
                  style={{ padding: "0.75rem", borderRadius: "8px", border: "1px solid var(--border-color)", fontSize: "0.875rem", outline: "none", fontFamily: "inherit" }}
                  placeholder="e.g. Department of Computer Science"
                  value={form.institutionName}
                  onChange={(e) => updateField("institutionName", e.target.value)}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <label htmlFor="university" style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--textMid)" }}>University</label>
                <input
                  id="university"
                  type="text"
                  style={{ padding: "0.75rem", borderRadius: "8px", border: "1px solid var(--border-color)", fontSize: "0.875rem", outline: "none", fontFamily: "inherit" }}
                  placeholder="e.g. IIT Delhi"
                  value={form.university}
                  onChange={(e) => updateField("university", e.target.value)}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <label htmlFor="department" style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--textMid)" }}>Department</label>
                <input
                  id="department"
                  type="text"
                  style={{ padding: "0.75rem", borderRadius: "8px", border: "1px solid var(--border-color)", fontSize: "0.875rem", outline: "none", fontFamily: "inherit" }}
                  placeholder="e.g. Computer Science"
                  value={form.department}
                  onChange={(e) => updateField("department", e.target.value)}
                />
              </div>
            </>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: "100%", marginTop: "0.5rem", justifyContent: "center", padding: "0.875rem" }}
            disabled={loading}
          >
            {loading ? "Creating account…" : "Create Account"}
          </button>
        </form>

        <div style={{ margin: "1.5rem 0", display: "flex", alignItems: "center", textAlign: "center", color: "var(--border-color)" }}>
          <div style={{ flex: 1, height: "1px", background: "var(--border-color)" }}></div>
          <span style={{ padding: "0 10px", color: "var(--textLight)", fontSize: "0.875rem" }}>or</span>
          <div style={{ flex: 1, height: "1px", background: "var(--border-color)" }}></div>
        </div>

        <p style={{ textAlign: "center", fontSize: "0.875rem", color: "var(--textMid)" }}>
          Already have an account?{" "}
          <Link href="/login" style={{ color: "var(--blue)", textDecoration: "none", fontWeight: 600 }}>
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
