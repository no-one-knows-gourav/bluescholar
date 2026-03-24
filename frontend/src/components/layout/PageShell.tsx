"use client";

import { ReactNode } from "react";

interface PageShellProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}

export default function PageShell({ title, subtitle, actions, children }: PageShellProps) {
  return (
    <div className="main-content">
      <div className="topbar">
        <div style={{ flex: 1 }}>
          <div className="topbar-title">{title}</div>
          {subtitle && (
            <div className="topbar-meta">{subtitle}</div>
          )}
        </div>
        {actions && (
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            {actions}
          </div>
        )}
      </div>

      <div className="page-content">
        {children}
      </div>
    </div>
  );
}
