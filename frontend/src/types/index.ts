export interface User {
  id: string;
  display_name: string;
  email: string;
  role: string;
  status: string;
  created_at: string;
}

export interface Lesson {
  slug: string;
  title: string;
  module_number: number;
  lesson_number: number;
  module_title: string;
  difficulty: number;
  estimated_minutes: number;
  status: 'not_started' | 'in_progress' | 'completed' | 'skipped';
  roadmap_status?: 'locked' | 'available' | 'completed' | null;
}

export interface Task {
  id: string;
  slug: string;
  title: string;
  description: string;
  difficulty: number;
  validation_strategy: string;
}

export interface TaskDetail {
  id: string;
  lesson_id: string;
  slug: string;
  title: string;
  description: string;
  instructions: string;
  expected_result_text: string | null;
  hint: string | null;
  difficulty: number;
  validation_strategy: string;
}

export interface ExecuteResult {
  columns: string[];
  rows: unknown[][];
  row_count: number;
  execution_time_ms: number;
  error?: string;
}

export interface SubmitResult {
  submission_id: string;
  attempt_number: number;
  is_correct: boolean;
  score: number;
  feedback: string;
  differences?: string[];
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Skill {
  id: string;
  code: string;
  title: string;
  description: string | null;
  category: string;
  icon: string;
  sort_order: number;
}

export interface StudentSkill {
  skill_id: string;
  skill_code: string;
  skill_title: string;
  skill_icon: string;
  skill_category: string;
  percentage: number | string;
  confidence: number | string;
  total_attempts: number;
  successful_attempts: number;
  last_practiced_at: string | null;
}

export interface SkillAnalysis {
  overall_level: number;
  level_label: string;
  studied_count: number;
  strong: StudentSkill[];
  weak: StudentSkill[];
  fading: StudentSkill[];
  unstudied: StudentSkill[];
}

export interface TaskSkillTag {
  code: string;
  title: string;
  weight: number;
}

export interface TaskWithSkills {
  id: string;
  slug: string;
  title: string;
  description: string;
  difficulty: number;
  skills: TaskSkillTag[];
}

export interface SubmitResultEnhanced extends SubmitResult {
  skill_updates?: { code: string; score: number }[];
}

export interface StudentMistake {
  id: string;
  mistake_type_id: string;
  mistake_code: string;
  mistake_title: string;
  skill_id: string | null;
  title: string;
  details: string | null;
  severity: number;
  repeat_count: number;
  status: 'new' | 'active' | 'training' | 'resolved' | 'ignored';
  first_seen_at: string;
  last_seen_at: string;
  resolved_at: string | null;
}

export interface MistakeType {
  id: string;
  code: string;
  title: string;
  description: string | null;
  domain: string;
  severity_default: number;
}