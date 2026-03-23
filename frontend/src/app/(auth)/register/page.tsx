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
    <div className="auth-container">
      <div className="auth-card animate-fade-in" style={{ maxWidth: 500 }}>
        <h1>Create Account</h1>
        <p className="subtitle">Join BlueScholar as a student or faculty</p>

        {error && (
          <div
            style={{
              background: "var(--accent-red-light)",
              color: "var(--accent-red)",
              padding: "0.75rem 1rem",
              borderRadius: "var(--radius)",
              fontSize: "0.875rem",
              marginBottom: "1.25rem",
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Role selector */}
          <div className="form-group">
            <label>I am a</label>
            <div style={{ display: "flex", gap: "0.75rem" }}>
              {(["student", "faculty"] as const).map((role) => (
                <button
                  key={role}
                  type="button"
                  className={`btn ${form.role === role ? "btn-primary" : "btn-secondary"}`}
                  style={{ flex: 1, textTransform: "capitalize" }}
                  onClick={() => updateField("role", role)}
                >
                  {role}
                </button>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="fullName">Full Name</label>
            <input
              id="fullName"
              type="text"
              className="input"
              placeholder="Your full name"
              value={form.fullName}
              onChange={(e) => updateField("fullName", e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="reg-email">Email</label>
            <input
              id="reg-email"
              type="email"
              className="input"
              placeholder="you@university.edu"
              value={form.email}
              onChange={(e) => updateField("email", e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="reg-password">Password</label>
            <input
              id="reg-password"
              type="password"
              className="input"
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
              <div className="form-group">
                <label htmlFor="rollNumber">Roll Number</label>
                <input
                  id="rollNumber"
                  type="text"
                  className="input"
                  placeholder="e.g. 21CS3045"
                  value={form.rollNumber}
                  onChange={(e) => updateField("rollNumber", e.target.value)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="enrollmentCode">Enrollment Code</label>
                <input
                  id="enrollmentCode"
                  type="text"
                  className="input"
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
              <div className="form-group">
                <label htmlFor="institutionName">Institution Name</label>
                <input
                  id="institutionName"
                  type="text"
                  className="input"
                  placeholder="e.g. Department of Computer Science"
                  value={form.institutionName}
                  onChange={(e) => updateField("institutionName", e.target.value)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="university">University</label>
                <input
                  id="university"
                  type="text"
                  className="input"
                  placeholder="e.g. IIT Delhi"
                  value={form.university}
                  onChange={(e) => updateField("university", e.target.value)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="department">Department</label>
                <input
                  id="department"
                  type="text"
                  className="input"
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
            style={{ width: "100%", marginTop: "0.5rem" }}
            disabled={loading}
          >
            {loading ? "Creating account…" : "Create Account"}
          </button>
        </form>

        <div className="form-divider">or</div>

        <p style={{ textAlign: "center", fontSize: "0.875rem", color: "var(--text-secondary)" }}>
          Already have an account?{" "}
          <Link href="/login" style={{ color: "var(--accent-blue)", textDecoration: "none", fontWeight: 500 }}>
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
