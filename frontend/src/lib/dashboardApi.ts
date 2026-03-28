export interface Profile {
  name: string;
  avatarUrl?: string;
}

export interface ContentManagerData {
  tools: string[];
  courses: { id: string; name: string }[];
}

export interface TodoItem {
  id: string;
  text: string;
  completed: boolean;
}

export interface StudyPlannerData {
  month: string;
  year: number;
  highlightedDates: number[];
  selectedDate: number;
  todos: TodoItem[];
}

export interface TimerData {
  display: string;
  activeTab: string;
}

export interface AnalyticsData {
  readiness: number;
  completed: number;
  engagementHistory: number[];
  categories: string[];
}

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

export async function fetchProfile(): Promise<Profile> {
  await delay(100);
  return { name: "Bhavya Bharadwaj" };
}

export async function fetchContentManager(): Promise<ContentManagerData> {
  await delay(100);
  return {
    tools: [
      "Ask Assistant",
      "Summarize",
      "AutoResearch",
      "View Syllabus",
      "Generate Mock",
      "Create Exam Folder",
      "Digest Lectures",
      "Quick Notes",
      "Practice Questions",
    ],
    courses: Array.from({ length: 12 }, (_, i) => ({
      id: `course-${i + 1}`,
      name: "Course Name",
    })),
  };
}

export async function fetchStudyPlanner(): Promise<StudyPlannerData> {
  await delay(100);
  return {
    month: "June",
    year: 2025,
    highlightedDates: [17, 18, 19],
    selectedDate: 12,
    todos: [
      { id: "1", text: "To-do 1 coursework", completed: false },
      { id: "2", text: "To-do 1 course", completed: false },
      { id: "3", text: "To-do 1 habit tracking", completed: false },
      { id: "4", text: "To-do 1 travelling", completed: false },
      { id: "5", text: "To-do 1", completed: false },
    ],
  };
}

export async function fetchTimer(): Promise<TimerData> {
  await delay(100);
  return { display: "10:10:10", activeTab: "time" };
}

export async function fetchAnalytics(): Promise<AnalyticsData> {
  await delay(100);
  return {
    readiness: 67,
    completed: 20,
    engagementHistory: [40, 65, 50, 80, 55, 70, 45],
    categories: [
      "Ask Assistant",
      "History",
      "Readiness",
      "Mock Analysis",
      "Subject-wise",
      "Topic-wise",
    ],
  };
}
