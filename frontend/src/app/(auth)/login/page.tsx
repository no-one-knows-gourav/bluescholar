"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const supabase = createClient();
    const { data, error: authError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (authError) {
      setError(authError.message);
      setLoading(false);
      return;
    }

    // Redirect based on role
    const role = data.user?.user_metadata?.role || "student";
    router.push(role === "faculty" ? "/faculty/dashboard" : "/student/dashboard");
  }

  return (
    <div style={{ display: "flex", flex: 1, width: "100%", alignItems: "center", justifyContent: "center", minHeight: "100vh", padding: "2rem" }}>
      <div className="card card-lg animate-fade-in" style={{ width: "100%", maxWidth: 400 }}>
        <h1 className="serif" style={{ fontSize: "2rem", marginBottom: "0.25rem", color: "var(--navy)" }}>Welcome back</h1>
        <p style={{ color: "var(--textLight)", fontSize: "0.875rem", marginBottom: "1.5rem" }}>Sign in to your BlueScholar account</p>

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
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <label htmlFor="email" style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--textMid)" }}>Email</label>
            <input
              id="email"
              type="email"
              style={{ padding: "0.75rem", borderRadius: "8px", border: "1px solid var(--border-color)", fontSize: "0.875rem", outline: "none", fontFamily: "inherit" }}
              placeholder="you@university.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <label htmlFor="password" style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--textMid)" }}>Password</label>
            <input
              id="password"
              type="password"
              style={{ padding: "0.75rem", borderRadius: "8px", border: "1px solid var(--border-color)", fontSize: "0.875rem", outline: "none", fontFamily: "inherit" }}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: "100%", marginTop: "0.5rem", justifyContent: "center", padding: "0.875rem" }}
            disabled={loading}
          >
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        <div style={{ margin: "1.5rem 0", display: "flex", alignItems: "center", textAlign: "center", color: "var(--border-color)" }}>
          <div style={{ flex: 1, height: "1px", background: "var(--border-color)" }}></div>
          <span style={{ padding: "0 10px", color: "var(--textLight)", fontSize: "0.875rem" }}>or</span>
          <div style={{ flex: 1, height: "1px", background: "var(--border-color)" }}></div>
        </div>

        <p style={{ textAlign: "center", fontSize: "0.875rem", color: "var(--textMid)" }}>
          Don&apos;t have an account?{" "}
          <Link href="/register" style={{ color: "var(--blue)", textDecoration: "none", fontWeight: 600 }}>
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
