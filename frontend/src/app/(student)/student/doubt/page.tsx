"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import PageShell from "@/components/layout/PageShell";
import {
  MessageSquare,
  Send,
  FileText,
  Sparkles,
  Loader2,
  BookOpen,
  ExternalLink,
} from "lucide-react";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceCitation[];
  timestamp: Date;
}

interface SourceCitation {
  filename: string;
  page: number | string | null;
  score: number;
  text_preview: string;
  source_type: string;
}

export default function DocDoubtPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeSources, setActiveSources] = useState<SourceCitation[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  async function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault();
    if (!input.trim() || isStreaming) return;

    const question = input.trim();
    setInput("");

    // Add user message
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsStreaming(true);

    // Prepare assistant placeholder
    const assistantId = crypto.randomUUID();
    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      sources: [],
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      const apiUrl =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/v1/student/doubt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No reader available");

      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;

          try {
            const event = JSON.parse(jsonStr);

            if (event.type === "sources") {
              setActiveSources(event.data || []);
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, sources: event.data }
                    : m
                )
              );
            } else if (event.type === "text") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, content: m.content + event.data }
                    : m
                )
              );
            }
          } catch {
            // Skip malformed JSON
          }
        }
      }
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content:
                  "⚠ Connection error. Please check that the backend is running and try again.",
              }
            : m
        )
      );
    } finally {
      setIsStreaming(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <PageShell
      title="DocDoubt"
      subtitle="Ask questions grounded in your uploaded study material"
    >
      <div className="doubt-layout">
        {/* Chat Panel */}
        <div className="doubt-chat">
          <div className="chat-container" style={{ height: "calc(100vh - 220px)" }}>
            <div className="chat-messages">
              {messages.length === 0 && (
                <div className="doubt-empty-state">
                  <div className="doubt-empty-icon">
                    <MessageSquare size={32} />
                  </div>
                  <h3>Ask DocDoubt anything</h3>
                  <p>
                    Your questions are answered strictly from your uploaded
                    notes and course materials. Every answer includes source
                    citations.
                  </p>
                  <div className="doubt-suggestions">
                    {[
                      "Explain the key concepts in Unit 2",
                      "What are the differences between TCP and UDP?",
                      "Summarize the main theorems from my notes",
                      "How is backpropagation calculated?",
                    ].map((q) => (
                      <button
                        key={q}
                        className="doubt-suggestion"
                        onClick={() => {
                          setInput(q);
                          inputRef.current?.focus();
                        }}
                      >
                        <Sparkles size={12} />
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`chat-msg ${msg.role === "user" ? "user" : "ai"}`}
                >
                  <div
                    className={`chat-avatar ${msg.role === "user" ? "user-av" : "ai"}`}
                  >
                    {msg.role === "user" ? "Y" : "D"}
                  </div>
                  <div>
                    <div className="chat-bubble">
                      {msg.content || (
                        <div className="loading-dots">
                          <div className="loading-dot" />
                          <div className="loading-dot" />
                          <div className="loading-dot" />
                        </div>
                      )}
                    </div>
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="doubt-citations">
                        {msg.sources.slice(0, 3).map((src, i) => (
                          <span key={i} className="citation-chip">
                            <FileText size={10} />
                            {src.filename}
                            {src.page && src.page !== "?" && (
                              <span className="citation-page">
                                p.{src.page}
                              </span>
                            )}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            <form className="chat-input-area" onSubmit={handleSubmit}>
              <textarea
                ref={inputRef}
                className="chat-input"
                placeholder="Ask a question about your study material..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                disabled={isStreaming}
              />
              <button
                type="submit"
                className="btn btn-primary"
                disabled={!input.trim() || isStreaming}
                style={{
                  padding: "8px 12px",
                  borderRadius: "8px",
                  height: "36px",
                }}
              >
                {isStreaming ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Send size={16} />
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Sources Panel */}
        <div className="doubt-sources">
          <div className="card" style={{ height: "calc(100vh - 220px)", overflow: "auto" }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                marginBottom: "16px",
              }}
            >
              <BookOpen size={16} style={{ color: "var(--blue)" }} />
              <h3 className="card-title" style={{ margin: 0, fontSize: "14px" }}>
                Source Context
              </h3>
            </div>

            {activeSources.length === 0 ? (
              <div
                style={{
                  color: "var(--slateLight)",
                  fontSize: "13px",
                  textAlign: "center",
                  padding: "40px 20px",
                }}
              >
                <FileText
                  size={28}
                  style={{ marginBottom: "12px", opacity: 0.3 }}
                />
                <p>Source documents will appear here when you ask a question.</p>
              </div>
            ) : (
              <div
                style={{ display: "flex", flexDirection: "column", gap: "10px" }}
              >
                {activeSources.map((src, i) => (
                  <div key={i} className="source-card">
                    <div className="source-header">
                      <span className="source-filename">
                        <FileText size={12} />
                        {src.filename}
                      </span>
                      <span className="source-score">
                        {Math.round(src.score * 100)}% match
                      </span>
                    </div>
                    {src.page && src.page !== "?" && (
                      <span
                        className="badge badge-blue"
                        style={{ fontSize: "10px", marginBottom: "6px" }}
                      >
                        Page {src.page}
                      </span>
                    )}
                    {src.text_preview && (
                      <p className="source-preview">{src.text_preview}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </PageShell>
  );
}
