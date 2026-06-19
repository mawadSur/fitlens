export type Consultant = {
  id: number;
  name: string;
  email: string;
  visa_status: string;
  status: string;
  primary_skill: string;
  skills: string[];
  years_experience: number;
  expected_rate: number;
  location: string;
  availability_date: string | null;
  days_until_available: number | null;
  days_on_bench: number;
  daily_bench_cost: number;
  resumes?: { id: number; filename: string; parsed_skills: string[]; is_primary: boolean; has_embedding: boolean }[];
  immigration?: Record<string, unknown>;
};

export type Match = {
  job_id: number;
  title: string;
  client: string;
  location: string;
  rate_band: [number, number];
  source: string;
  match_score: number;
  semantic: number;
  skill_overlap: number;
  rate_fit: number;
  visa_eligible: boolean;
  vendor_score: number;
  interview_probability: number;
  placement_probability: number;
};

export type Job = {
  id: number;
  title: string;
  client: string;
  location: string;
  remote: boolean;
  required_skills: string[];
  rate_band: [number, number];
  visa_requirements: string[];
  source: string;
  status: string;
};

export type Submission = {
  id: number;
  consultant_name: string;
  job_title: string;
  rate: number;
  status: string;
  match_score: number;
  submitted_at: string | null;
};

export type Dashboard = {
  counts: Record<string, number>;
  hot_bench: any[];
  bench_alerts: string[];
  total_daily_bench_cost: number;
  immigration_alerts: string[];
  revenue_forecast: Record<string, number>;
  top_placements: any[];
};

export type Integration = {
  embedder_backend: string;
  live_count: number;
  total: number;
  connectors: { name: string; category: string; live: boolean; missing_credentials: string[]; note: string }[];
};
