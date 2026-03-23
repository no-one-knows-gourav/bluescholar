"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

interface CourseFile {
  name: string;
  size: number;
  status: "uploading" | "processing" | "ready" | "error";
}

export default function FacultyCourseware() {
  const [files, setFiles] = useState<CourseFile[]>([]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const newFiles: CourseFile[] = acceptedFiles.map((f) => ({
      name: f.name,
      size: f.size,
      status: "uploading" as const,
    }));
    setFiles((prev) => [...newFiles, ...prev]);

    const formData = new FormData();
    acceptedFiles.forEach((f) => formData.append("files", f));

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/v1/faculty/courseware/upload`, {
        method: "POST",
        body: formData,
      });

      setFiles((prev) =>
        prev.map((f) =>
          newFiles.some((nf) => nf.name === f.name)
            ? { ...f, status: res.ok ? ("processing" as const) : ("error" as const) }
            : f
        )
      );
    } catch {
      setFiles((prev) =>
        prev.map((f) =>
          newFiles.some((nf) => nf.name === f.name) ? { ...f, status: "error" as const } : f
        )
      );
    }
  }, []);

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
          <h1>Courseware</h1>
          <p className="subtitle">Upload and manage course materials for your institutional knowledge base</p>
        </div>
      </div>

      <div
        {...getRootProps()}
        className={`upload-zone ${isDragActive ? "active" : ""}`}
        style={{ marginBottom: "2rem" }}
      >
        <input {...getInputProps()} />
        <div style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>
          {isDragActive ? "📥" : "📖"}
        </div>
        <p style={{ fontWeight: 500, marginBottom: "0.25rem" }}>
          {isDragActive ? "Drop course materials here" : "Upload course materials"}
        </p>
        <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
          These materials will be available to all enrolled students via DocDoubt
        </p>
      </div>

      {files.length > 0 && (
        <div>
          <h3 style={{ marginBottom: "1rem" }}>Course Materials</h3>
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
                  <span style={{ fontSize: "1.25rem" }}>📄</span>
                  <div>
                    <p style={{ fontWeight: 500, fontSize: "0.875rem" }}>{file.name}</p>
                    <p className="mono" style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                <span
                  className={`badge ${file.status === "ready" ? "badge-green"
                      : file.status === "error" ? "badge-red"
                        : file.status === "processing" ? "badge-amber"
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

      {files.length === 0 && (
        <div className="card" style={{ textAlign: "center", padding: "3rem", color: "var(--text-secondary)" }}>
          <p style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>📖</p>
          <p>No course materials uploaded yet.</p>
          <p style={{ fontSize: "0.8125rem", marginTop: "0.25rem" }}>
            Upload notes, slides, textbooks. They&apos;ll be chunked, embedded, and made searchable for your students.
          </p>
        </div>
      )}
    </div>
  );
}
