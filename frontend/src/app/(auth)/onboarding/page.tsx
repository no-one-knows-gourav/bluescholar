"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

export default function OnboardingPage() {
  const router = useRouter();
  const [role, setRole] = useState<string | null>(null);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => {
      const userRole = data.user?.user_metadata?.role || "student";
      setRole(userRole);
    });
  }, []);

  function handleContinue() {
    if (role === "faculty") {
      router.push("/faculty/dashboard");
    } else {
      router.push("/student/dashboard");
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card animate-fade-in" style={{ maxWidth: 560, textAlign: "center" }}>
        <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🎓</div>
        <h1>Welcome to BlueScholar!</h1>
        <p className="subtitle" style={{ marginBottom: "2rem" }}>
          {role === "faculty"
            ? "You're all set up as faculty. Upload your course materials to get started."
            : "Your account is ready. Upload your syllabus to unlock personalized preparation."}
        </p>

        <div className="card" style={{ textAlign: "left", marginBottom: "1.5rem" }}>
          <h3 style={{ marginBottom: "1rem" }}>
            {role === "faculty" ? "Next Steps" : "Get Started"}
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {role === "faculty" ? (
              <>
                <StepItem number={1} text="Upload your course materials (notes, slides, textbooks)" />
                <StepItem number={2} text="Share your enrollment code with students" />
                <StepItem number={3} text="Create exams and monitor student progress" />
              </>
            ) : (
              <>
                <StepItem number={1} text="Upload your syllabus PDF to map your course" />
                <StepItem number={2} text="Upload notes, slides, and past papers" />
                <StepItem number={3} text="Start preparing with AI-powered tools" />
              </>
            )}
          </div>
        </div>

        <button className="btn btn-primary" onClick={handleContinue} style={{ width: "100%" }}>
          Go to Dashboard →
        </button>
      </div>
    </div>
  );
}

function StepItem({ number, text }: { number: number; text: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: "50%",
          background: "var(--accent-blue-light)",
          color: "var(--accent-blue)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "0.75rem",
          fontWeight: 600,
          flexShrink: 0,
        }}
      >
        {number}
      </div>
      <span style={{ fontSize: "0.875rem", color: "var(--text-primary)" }}>{text}</span>
    </div>
  );
}
