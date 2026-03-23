"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

interface UploadedFile {
  name: string;
  size: number;
  status: "uploading" | "processing" | "ready" | "error";
}

export default function StudentLibrary() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [docType, setDocType] = useState<string>("student_note");

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      // Add files to local state immediately
      const newFiles: UploadedFile[] = acceptedFiles.map((f) => ({
        name: f.name,
        size: f.size,
        status: "uploading" as const,
      }));
      setFiles((prev) => [...newFiles, ...prev]);

      // Upload to backend
      const formData = new FormData();
      acceptedFiles.forEach((f) => formData.append("files", f));

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/api/v1/student/upload?doc_type=${docType}`, {
          method: "POST",
          body: formData,
          // TODO: Add auth header from Supabase session
        });

        if (res.ok) {
          setFiles((prev) =>
            prev.map((f) =>
              newFiles.some((nf) => nf.name === f.name)
                ? { ...f, status: "processing" as const }
                : f
            )
          );
        } else {
          setFiles((prev) =>
            prev.map((f) =>
              newFiles.some((nf) => nf.name === f.name)
                ? { ...f, status: "error" as const }
                : f
            )
          );
        }
      } catch {
        setFiles((prev) =>
          prev.map((f) =>
            newFiles.some((nf) => nf.name === f.name)
              ? { ...f, status: "error" as const }
              : f
          )
        );
      }
    },
    [docType]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
      "image/*": [".png", ".jpg", ".jpeg"],
      "text/plain": [".txt"],
    },
    multiple: true,
  });

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <div>
          <h1>Library</h1>
          <p className="subtitle">Upload and manage your study materials</p>
        </div>
      </div>

      {/* Document type selector */}
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem" }}>
        {[
          { value: "student_note", label: "Notes" },
          { value: "syllabus", label: "Syllabus" },
          { value: "past_paper", label: "Past Paper" },
        ].map((opt) => (
          <button
            key={opt.value}
            className={`btn ${docType === opt.value ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setDocType(opt.value)}
            style={{ fontSize: "0.8125rem" }}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Upload zone */}
      <div
        {...getRootProps()}
        className={`upload-zone ${isDragActive ? "active" : ""}`}
        style={{ marginBottom: "2rem" }}
      >
        <input {...getInputProps()} />
        <div className="icon" style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>
          {isDragActive ? "📥" : "📤"}
        </div>
        <p style={{ fontWeight: 500, marginBottom: "0.25rem" }}>
          {isDragActive ? "Drop files here" : "Drag & drop files, or click to browse"}
        </p>
        <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
          Supports PDF, DOCX, PPTX, PNG, JPG, TXT
        </p>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div>
          <h3 style={{ marginBottom: "1rem" }}>Uploaded Files</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {files.map((file, i) => (
              <div
                key={`${file.name}-${i}`}
                className="card"
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0.875rem 1.25rem",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <span style={{ fontSize: "1.25rem" }}>
                    {file.name.endsWith(".pdf")
                      ? "📕"
                      : file.name.endsWith(".docx")
                        ? "📘"
                        : file.name.endsWith(".pptx")
                          ? "📙"
                          : "📄"}
                  </span>
                  <div>
                    <p style={{ fontWeight: 500, fontSize: "0.875rem" }}>{file.name}</p>
                    <p className="mono" style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                <span
                  className={`badge ${file.status === "ready"
                      ? "badge-green"
                      : file.status === "error"
                        ? "badge-red"
                        : file.status === "processing"
                          ? "badge-amber"
                          : "badge-blue"
                    }`}
                >
                  {file.status === "uploading" && "⬆ Uploading"}
                  {file.status === "processing" && "⏳ Processing"}
                  {file.status === "ready" && "✓ Ready"}
                  {file.status === "error" && "✗ Error"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {files.length === 0 && (
        <div className="card" style={{ textAlign: "center", padding: "3rem", color: "var(--text-secondary)" }}>
          <p style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>📚</p>
          <p>Your library is empty.</p>
          <p style={{ fontSize: "0.8125rem", marginTop: "0.25rem" }}>
            Upload notes, slides, and past papers to get started with AI-powered study tools.
          </p>
        </div>
      )}
    </div>
  );
}
