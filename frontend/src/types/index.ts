export type User = {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  auth_provider: string;
  is_active: boolean;
  is_verified: boolean;
  theme: string;
  visa_sponsorship_required: boolean;
  created_at: string;
};

export type CompanyBrief = {
  id: string;
  name: string;
  slug: string;
  logo_url: string | null;
  website: string | null;
  industry: string | null;
  company_size: string | null;
  offers_visa_sponsorship: boolean | null;
};

export type Job = {
  id: string;
  title: string;
  country: string | null;
  city: string | null;
  work_mode: string | null;
  employment_type: string | null;
  experience_level: string | null;
  visa_sponsorship: boolean;
  relocation: boolean;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  salary_estimated: boolean;
  source: string;
  apply_url: string | null;
  posted_at: string | null;
  match_score: number | null;
  recommendation_score: number | null;
  recommendation_priority: string | null;
  company: CompanyBrief | null;
  description?: string | null;
  responsibilities?: string | null;
  requirements?: string | null;
  preferred_skills?: string | null;
  benefits?: string | null;
  technology_stack?: string | null;
  location_raw?: string | null;
  source_url?: string | null;
  expires_at?: string | null;
  is_active?: boolean;
  created_at?: string;
};

export type PaginatedJobs = {
  items: Job[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type DashboardStats = {
  total_jobs: number;
  jobs_added_today: number;
  remote_jobs: number;
  visa_sponsorship_jobs: number;
  average_salary: number | null;
  countries_count: number;
  companies_hiring: number;
  saved_jobs: number;
  applications: number;
  recommended_jobs: number;
};

export type ActivityItem = {
  id: string;
  type: string;
  title: string;
  subtitle: string | null;
  timestamp: string;
  link: string | null;
};

// ── Resume ────────────────────────────────────────────────────────────────────

export type Resume = {
  id: string;
  filename: string;
  file_url: string | null;
  is_primary: boolean;
  parsed_skills: string[] | null;
  parsed_experience: string | null;
  parsed_education: string | null;
  raw_text: string | null;
  created_at: string;
  updated_at: string;
};

// ── Match ─────────────────────────────────────────────────────────────────────

export type MatchScore = {
  overall: number;
  skill_match: number;
  experience_match: number;
  education_match: number;
  technology_match: number;
  ats_score: number;
  missing_skills: string[];
  missing_keywords: string[];
  strengths: string[];
  weaknesses: string[];
  matching_skills: string[];
};

// ── Recommendations ───────────────────────────────────────────────────────────

export type PaginatedRecommendations = {
  items: Job[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

// ── Salary ────────────────────────────────────────────────────────────────────

export type SalaryEstimate = {
  min: number;
  max: number;
  median: number;
  currency: string;
  country: string;
  experience_level: string;
  technologies: string[];
};

export type SalaryInsight = {
  technology: string;
  demand_score: number;
  avg_salary: number;
  currency: string;
  country: string;
  job_count: number;
};

// ── Skill Gap ─────────────────────────────────────────────────────────────────

export type SkillGapItem = {
  skill: string;
  priority: "high" | "medium" | "low";
  learning_hours: number;
  courses: { title: string; url: string; provider: string }[];
  docs: { title: string; url: string }[];
  projects: string[];
  match_improvement: number;
};

// ── Applications ──────────────────────────────────────────────────────────────

export type ApplicationStatus =
  | "saved"
  | "applied"
  | "screening"
  | "interview"
  | "offer"
  | "rejected"
  | "withdrawn";

export type Application = {
  id: string;
  job_id: string;
  job: Job | null;
  status: ApplicationStatus;
  notes: string | null;
  applied_at: string | null;
  created_at: string;
  updated_at: string;
};

// ── Alerts ────────────────────────────────────────────────────────────────────

export type Alert = {
  id: string;
  name: string;
  keywords: string[];
  countries: string[];
  work_modes: string[];
  min_salary: number | null;
  channels: string[];
  is_active: boolean;
  created_at: string;
};

// ── Notifications ─────────────────────────────────────────────────────────────

export type Notification = {
  id: string;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  link: string | null;
  created_at: string;
};

// ── Analytics ─────────────────────────────────────────────────────────────────

export type AnalyticsOverview = {
  applications_over_time: { date: string; count: number }[];
  jobs_by_country: { country: string; count: number }[];
  tech_demand: { technology: string; count: number }[];
  match_distribution: { range: string; count: number }[];
  status_breakdown: { status: string; count: number }[];
};

// ── AI Features ───────────────────────────────────────────────────────────────

export type CoverLetterResult = {
  content: string;
  job_title?: string;
  company_name?: string;
};

export type OptimizeResult = {
  optimized_resume: string;
  improvements: string[];
  ats_score_before: number;
  ats_score_after: number;
  matching_skills?: string[];
  missing_skills?: string[];
};

export type InterviewPrep = {
  questions: { question: string; hint: string | null; category: string }[];
  topics: string[];
  job_title?: string;
};

// ── Live View ─────────────────────────────────────────────────────────────────

export type LiveView = {
  job: Job;
  resume: Resume | null;
  matching_skills: string[];
  missing_skills: string[];
  matching_keywords: string[];
};

// ── Recruiters ────────────────────────────────────────────────────────────────

export type Recruiter = {
  id: string;
  name: string;
  company: CompanyBrief | null;
  email: string | null;
  linkedin_url: string | null;
  specialization: string | null;
  note?: string;
  created_at: string;
};
