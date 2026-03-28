"use client";

import { usePathname } from "next/navigation";
import Sidebar from "@/components/Sidebar";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isDashboard = pathname === "/student/dashboard";

  if (isDashboard) {
    return <>{children}</>;
  }

  return (
    <div className="flex">
      <Sidebar role="student" />
      <div className="flex-1 w-full">
        <main className="main-content">{children}</main>
      </div>
    </div>
  );
}
