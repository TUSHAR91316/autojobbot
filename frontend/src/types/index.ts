export interface CandidateProfile {
  id: number;
  full_name: string;
  email: string;
  phone: string;
  current_location: string;
  headline: string;
  summary: string;
  skills: string[];
  work_experience: Array<{
    title: string;
    company: string;
    location: string;
    start_date: string;
    end_date: string;
    current: boolean;
    description: string;
  }>;
  education: Array<{
    degree: string;
    institution: string;
    field_of_study: string;
    graduation_year: string;
    gpa: string;
  }>;
  projects: Array<{
    name: string;
    description: string;
    url: string;
    technologies: string[];
  }>;
  certifications: Array<{
    name: string;
    issuer: string;
    issue_date: string;
    url: string;
  }>;
  portfolio_url: string;
  github_url: string;
  linkedin_url: string;
  preferred_job_titles: string[];
  preferred_locations: string[];
  remote_preference: string;
  salary_expectation_min: number;
  salary_expectation_max: number;
  salary_currency: string;
  years_of_experience: number;
  experience_level: string;
  employment_types: string[];
  created_at: string;
  updated_at: string;
}

export interface ResumeVersion {
  id: number;
  label: string;
  target_categories: string[];
  file_name: string;
  file_path: string;
  file_size: number;
  file_type: string;
  extracted_text: string;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface JobListing {
  id: number;
  title: string;
  company: string;
  location: string;
  work_mode: string;
  employment_type: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency: string;
  experience_min_years: number;
  experience_level: string;
  required_skills: string[];
  description: string;
  source_platform: string;
  original_url: string;
  normalized_url: string;
  source_job_id?: string;
  application_method: string;
  match_score: number;
  match_breakdown: {
    skills_score?: number;
    skills_weight?: number;
    matched_skills?: string[];
    missing_skills?: string[];
    title_score?: number;
    title_weight?: number;
    experience_score?: number;
    experience_weight?: number;
    location_score?: number;
    location_weight?: number;
    employment_type_score?: number;
    employment_type_weight?: number;
  };
  eligibility_assessment: {
    is_eligible: boolean;
    reasons: string[];
  };
  status: string;
  is_archived: boolean;
  discovered_at: string;
  updated_at: string;
}

export type ApplicationStatus =
  | "DISCOVERED"
  | "MATCHED"
  | "QUEUED"
  | "PREPARING"
  | "AWAITING_REVIEW"
  | "READY_TO_SUBMIT"
  | "SUBMITTED"
  | "FAILED"
  | "SKIPPED"
  | "MANUAL_ACTION_REQUIRED"
  | "CANCELLED";

export interface JobApplication {
  id: number;
  job_id: number;
  resume_version_id?: number;
  status: ApplicationStatus;
  queue_position: number;
  prepared_data: Record<string, any>;
  unanswered_questions: Array<Record<string, any>>;
  review_notes: string;
  cover_letter: string;
  manual_notes: string;
  external_portal_url: string;
  last_action: string;
  error_message: string;
  screenshot_path: string;
  session_id?: string;
  applied_at?: string;
  last_action_at: string;
  created_at: string;
  updated_at: string;
  job?: JobListing;
  resume?: ResumeVersion;
}

export interface AutomationSettings {
  id: number;
  target_applications_per_session: number;
  delay_between_attempts_sec: number;
  min_match_score: number;
  max_jobs_to_inspect: number;
  preferred_job_sources: string[];
  prioritize_easy_apply: boolean;
  include_external_in_manual_queue: boolean;
  require_review_before_submit: boolean;
  stop_after_failures: number;
  skip_duplicates: boolean;
  stop_on_captcha_mfa: boolean;
  simulation_mode: boolean;
  log_retention_days: number;
  updated_at: string;
}

export interface JobPreferences {
  id: number;
  title_keywords: string[];
  negative_keywords: string[];
  preferred_locations: string[];
  remote_only: boolean;
  min_salary: number;
  max_salary: number;
  experience_level: string;
  required_skills: string[];
  preferred_companies: string[];
  excluded_companies: string[];
  weight_skills: number;
  weight_title: number;
  weight_experience: number;
  weight_location: number;
  weight_employment_type: number;
  updated_at: string;
}

export interface ActivityLog {
  id: number;
  level: string;
  action: string;
  message: string;
  details: Record<string, any>;
  job_id?: number;
  application_id?: number;
  created_at: string;
}

export interface SessionProgress {
  is_active: boolean;
  is_paused: boolean;
  status: "IDLE" | "RUNNING" | "PAUSED" | "STOPPING";
  target_count: number;
  processed_count: number;
  submitted_count: number;
  manual_count: number;
  failed_count: number;
  current_job_id?: number;
  current_job_title?: string;
  current_action?: string;
  session_id?: string;
  started_at?: string;
}

export interface DashboardStats {
  jobs_discovered: number;
  jobs_matching_preferences: number;
  applications_prepared: number;
  applications_submitted: number;
  applications_awaiting_review: number;
  external_manual_action_required: number;
  applications_failed_or_cancelled: number;
  status_distribution: Record<string, number>;
  source_distribution: Record<string, number>;
  session_progress: SessionProgress;
  last_run: {
    session_id?: string;
    started_at?: string;
    ended_at?: string;
    target: number;
    submitted: number;
    failed: number;
    manual: number;
    status: string;
  };
  recent_jobs: JobListing[];
  recent_activity: ActivityLog[];
}
