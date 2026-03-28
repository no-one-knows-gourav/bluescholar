"use client";

import { useState, useEffect } from "react";
import s from "./dashboard.module.css";
import {
  User, Menu, Pencil, Search, ChevronLeft, ChevronRight,
  ArrowUpRight, Clock, AlarmClock, Timer, Hourglass,
  MessageSquare, AlignLeft, Microscope, BookOpen, ClipboardList,
  FolderPlus, Headphones, StickyNote, HelpCircle,
  History, Target, BarChart2, PieChart, ListTree, Camera
} from "lucide-react";
import {
  fetchProfile, fetchContentManager, fetchStudyPlanner,
  fetchTimer, fetchAnalytics,
  type Profile, type ContentManagerData, type StudyPlannerData,
  type TimerData, type AnalyticsData,
} from "@/lib/dashboardApi";

/* ── icon maps ── */
const CM_ICONS: Record<string, React.ElementType> = {
  "Ask Assistant": MessageSquare,
  "Summarize": AlignLeft,
  "AutoResearch": Microscope,
  "View Syllabus": BookOpen,
  "Generate Mock": ClipboardList,
  "Create Exam Folder": FolderPlus,
  "Digest Lectures": Headphones,
  "Quick Notes": StickyNote,
  "Practice Questions": HelpCircle,
};

const ANALYSIS_ICONS: Record<string, React.ElementType> = {
  "Ask Assistant": MessageSquare,
  "History": History,
  "Readiness": Target,
  "Mock Analysis": BarChart2,
  "Subject-wise": PieChart,
  "Topic-wise": ListTree,
};

/* ── helpers ── */
const DAYS_HEADER = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function buildCalendar(month: number, year: number) {
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const weeks: (number | null)[][] = [];
  let week: (number | null)[] = Array(7).fill(null);
  let day = 1;
  for (let i = firstDay; i < 7 && day <= daysInMonth; i++) week[i] = day++;
  weeks.push(week);
  while (day <= daysInMonth) {
    week = Array(7).fill(null);
    for (let i = 0; i < 7 && day <= daysInMonth; i++) week[i] = day++;
    weeks.push(week);
  }
  return weeks;
}

/* ── SVG helpers ── */
function FolderSvg() {
  return (
    <svg className={s.folderIcon} viewBox="0 0 40 32" fill="none">
      <path d="M2 4a4 4 0 0 1 4-4h10l4 4h16a4 4 0 0 1 4 4v20a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V4z" fill="#1788ED" />
    </svg>
  );
}

function DonutChart({ value, label }: { value: number; label: string }) {
  const r = 16, circ = 2 * Math.PI * r;
  const offset = circ * (1 - value / 100);
  return (
    <div className={s.donutWrap}>
      <svg className={s.donutSvg} viewBox="0 0 38 38">
        <circle className={s.donutTrack} cx="19" cy="19" r={r} />
        <circle className={s.donutFill} cx="19" cy="19" r={r}
          strokeDasharray={`${circ - offset} ${offset}`} />
      </svg>
      <div className={s.donutValue}>{value}%</div>
      <div className={s.donutLabel}>{label}</div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════ */
export default function StudentDashboard() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [cm, setCm] = useState<ContentManagerData | null>(null);
  const [planner, setPlanner] = useState<StudyPlannerData | null>(null);
  const [timer, setTimerData] = useState<TimerData | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [clockTab, setClockTab] = useState("time");
  const [plannerView, setPlannerView] = useState("daily");
  const [activeAnalysis, setActiveAnalysis] = useState("Readiness");
  const [bannerImg, setBannerImg] = useState<string | null>("/dashboard-banner.png");

  useEffect(() => {
    fetchProfile().then(setProfile);
    fetchContentManager().then(setCm);
    fetchStudyPlanner().then(setPlanner);
    fetchTimer().then(setTimerData);
    fetchAnalytics().then(setAnalytics);
  }, []);

  const handleBannerUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setBannerImg(event.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const weeks = buildCalendar(5, 2025); // June = month 5

  return (
    <div className={s.dashboard}>
      {/* ═══ BANNER ═══ */}
      <section className={s.banner}>
        {bannerImg && <img src={bannerImg} alt="banner" className={s.bannerImg} />}
        <div className={s.bannerOverlay} />
        
        <label className={s.bannerUploadBtn}>
          <Camera size={12} />
          <span>Change Cover</span>
          <input 
            type="file" 
            accept="image/*" 
            onChange={handleBannerUpload} 
            style={{ display: "none" }} 
          />
        </label>

        <div className={s.searchWrap}>
          <div className={s.searchBox}>
            <Search size={12} style={{ color: "rgba(255,255,255,0.45)", flexShrink: 0 }} />
            <input placeholder="Search" />
          </div>
        </div>
        <div className={s.bannerGlow} />
      </section>

      {/* ═══ PROFILE ═══ */}
      <div className={s.profileRow}>
        <div className={s.avatar}>
          <User size={24} />
        </div>
        <h2 className={s.profileName}>{profile?.name ?? "Bhavya Bharadwaj"}</h2>
        <div className={s.profileActions}>
          <button className={s.iconBtn}><Menu size={16} /></button>
          <button className={s.iconBtn}><Pencil size={14} /></button>
        </div>
      </div>

      {/* ═══ MAIN GRID (Now Flexbox Horizontal Wrapping) ═══ */}
      <div className={s.mainGrid}>
        
        {/* ── LEFT: Study Planner ── */}
        <div className={s.col} style={{ flex: "1.6 1 0%" }}>
          <div className={s.card}>
            <div className={s.cardHeader}>
              <h4 className={s.cardTitle}>Injective Study Planner</h4>
              <button className={s.expandLink}>
                Expand <ArrowUpRight size={12} />
              </button>
            </div>
            <div className={s.plannerBody}>
              {/* Calendar */}
              <div className={s.calendarSection}>
                <div className={s.calendarNav}>
                  <button className={s.calNavBtn}><ChevronLeft size={12} /></button>
                  <span className={s.calMonth}>June 2025</span>
                  <button className={s.calNavBtn}><ChevronRight size={12} /></button>
                </div>
                <div className={s.calGrid}>
                  {DAYS_HEADER.map((d) => (
                    <div key={d} className={s.calDayHeader}>{d}</div>
                  ))}
                  {weeks.flat().map((day, i) => {
                    if (day === null) return <div key={`e${i}`} className={`${s.calDay} ${s.calDayEmpty}`} />;
                    const sel = day === planner?.selectedDate;
                    const hi = planner?.highlightedDates.includes(day);
                    return (
                      <div key={i} className={[
                        s.calDay,
                        sel ? s.calDaySelected : "",
                        hi ? s.calDayHighlighted : "",
                      ].join(" ")}>
                        {day}
                      </div>
                    );
                  })}
                </div>
                <div className={s.plannerFooter}>
                  <button className={s.btnPrimary} style={{ width: "100%" }}>View Events</button>
                  <button className={s.btnPrimary} style={{ width: "100%" }}>Schedule Events</button>
                </div>
              </div>

              {/* Right: Select dropdown + todos */}
              <div className={s.plannerRight}>
                <select 
                  className={s.plannerSelect}
                  value={plannerView}
                  onChange={(e) => setPlannerView(e.target.value)}
                >
                  <option value="daily">Daily Planner</option>
                  <option value="weekly">Weekly Planner</option>
                  <option value="monthly">Monthly Planner</option>
                </select>
                <div className={s.plannerLabel}>To-do List</div>
                <div className={s.todoList}>
                  {planner?.todos.map((td) => (
                    <div key={td.id} className={s.todoItem}>
                      <div className={s.todoCircle} />
                      <span>{td.text}</span>
                    </div>
                  ))}
                </div>
                <div className={s.plannerButtons}>
                  <button className={s.btnPrimary}>Edit Planner</button>
                  <button className={s.btnPrimary}>Mark as Complete</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── CENTER: Content Manager ── */}
        <div className={s.col} style={{ flex: "2.2 1 0%" }}>
          <div className={s.card}>
            <div className={s.cardHeader}>
              <h4 className={s.cardTitle}>Content manager</h4>
              <button className={s.expandLink}>
                Expand <ArrowUpRight size={12} />
              </button>
            </div>
            <div className={s.cmBody}>
              <div className={s.cmSidebar}>
                {cm?.tools.map((t) => {
                  const Icon = CM_ICONS[t] || MessageSquare;
                  return (
                    <div key={t} className={s.cmTool}>
                      <span className={s.cmToolIcon}><Icon size={10} /></span>
                      {t}
                    </div>
                  );
                })}
              </div>
              <div className={s.cmFolderGrid}>
                {cm?.courses.map((c) => (
                  <div key={c.id} className={s.cmFolder}>
                    <FolderSvg />
                    <span className={s.folderName}>{c.name}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className={s.cmFooter}>
              <button className={s.btnPrimary} style={{ width: "200px" }}>View File Manager</button>
              <button className={s.btnPrimary} style={{ width: "200px" }}>Upload Material</button>
            </div>
          </div>
        </div>

        {/* ── RIGHT: Clock + Analysis ── */}
        <div className={s.col} style={{ flex: "1.1 1 0%" }}>
          {/* Timer Card */}
          <div className={s.card} style={{ flex: "0.8 1 0%", justifyContent: "center" }}>
            <div className={s.clockTabs}>
              {[
                { id: "time", label: "Time", Icon: Clock },
                { id: "alarm", label: "Alarm", Icon: AlarmClock },
                { id: "timer", label: "Timer", Icon: Timer },
                { id: "stopwatch", label: "Stopwatch", Icon: Hourglass },
              ].map(({ id, label, Icon }) => (
                <button key={id}
                  className={`${s.clockTab} ${clockTab === id ? s.clockTabActive : ""}`}
                  onClick={() => setClockTab(id)}
                >
                  <Icon size={8} />
                  {label}
                </button>
              ))}
            </div>
            <div className={s.clockDisplay}>{timer?.display ?? "10:10:10"}</div>
            <div className={s.clockButtons}>
              <button className={s.btnPrimary} style={{ width: "100%" }}>Record Session</button>
              <button className={s.btnPrimary} style={{ width: "100%" }}>Enable Focus Sync</button>
            </div>
          </div>

          {/* Analysis */}
          <div className={s.card} style={{ flex: "1.2 1 0%" }}>
            <div className={s.cardHeader}>
              <h4 className={s.cardTitle}>Analysis</h4>
              <button className={s.expandLink}>
                Expand <ArrowUpRight size={12} />
              </button>
            </div>
            <div className={s.analysisBody}>
              <div className={s.analysisSidebar}>
                {analytics?.categories.map((cat) => {
                  const Icon = ANALYSIS_ICONS[cat] || BarChart2;
                  return (
                    <div key={cat}
                      className={`${s.analysisSidebarItem} ${activeAnalysis === cat ? s.analysisSidebarItemActive : ""}`}
                      onClick={() => setActiveAnalysis(cat)}
                    >
                      <Icon size={8} />
                      {cat}
                    </div>
                  );
                })}
              </div>
              <div className={s.analysisContent}>
                <div className={s.donutRow}>
                  <DonutChart value={analytics?.readiness ?? 67} label="Readiness" />
                  <DonutChart value={analytics?.completed ?? 20} label="Completed" />
                </div>
                <div className={s.barChartWrap}>
                  <div className={s.barChartLabel}>Engagement History</div>
                  <div className={s.barChart}>
                    {(analytics?.engagementHistory || [40, 65, 50, 80, 55, 70, 45]).map((h, i) => (
                      <div key={i} className={s.bar} style={{ height: `${h}%` }} />
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <div style={{ marginTop: 'auto', paddingTop: '10px' }}>
              <button className={`${s.btnPrimary} ${s.clockFullBtn}`}>
                View Session History
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
