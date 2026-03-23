import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/layout/TopBar";

export default function FacultyLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex">
      <Sidebar role="faculty" />
      <div className="flex-1 w-full bg-[var(--bg-canvas)]">
        <TopBar />
        <main className="main-content">{children}</main>
      </div>
    </div>
  );
}
