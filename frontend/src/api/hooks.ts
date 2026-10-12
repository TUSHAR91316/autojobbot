import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";
import {
  CandidateProfile,
  ResumeVersion,
  JobListing,
  JobApplication,
  AutomationSettings,
  JobPreferences,
  ActivityLog,
  DashboardStats,
  SessionProgress,
} from "../types";

// Dashboard Stats
export const useDashboardStats = () => {
  return useQuery<DashboardStats>({
    queryKey: ["dashboard-stats"],
    queryFn: async () => {
      const res = await apiClient.get<DashboardStats>("/settings/dashboard-stats");
      return res.data;
    },
    refetchInterval: 3000, // Poll every 3s for live telemetry updates
  });
};

// Browser Sessions & Authentication Status
export interface BrowserSessionsStatus {
  linkedin: boolean;
  indeed: boolean;
  naukri: boolean;
  wellfound: boolean;
  google: boolean;
  total_cookies: number;
  profile_path: string;
  is_launched: boolean;
  is_cdp: boolean;
}

export const useBrowserSessions = () => {
  return useQuery<BrowserSessionsStatus>({
    queryKey: ["browser-sessions"],
    queryFn: async () => {
      const res = await apiClient.get<BrowserSessionsStatus>("/automation/browser/sessions");
      return res.data;
    },
    refetchInterval: 4000,
  });
};

// Automation Session Telemetry
export const useAutomationStatus = () => {
  return useQuery<SessionProgress>({
    queryKey: ["automation-status"],
    queryFn: async () => {
      const res = await apiClient.get<SessionProgress>("/automation/status");
      return res.data;
    },
    refetchInterval: 1500,
  });
};

// Jobs
export const useJobs = (params?: {
  search?: string;
  company?: string;
  work_mode?: string;
  min_score?: number;
  source_platform?: string;
  status?: string;
}) => {
  return useQuery<JobListing[]>({
    queryKey: ["jobs", params],
    queryFn: async () => {
      const res = await apiClient.get<JobListing[]>("/jobs", { params });
      return res.data;
    },
  });
};

export const useJobDetail = (jobId: number) => {
  return useQuery<JobListing>({
    queryKey: ["job", jobId],
    queryFn: async () => {
      const res = await apiClient.get<JobListing>(`/jobs/${jobId}`);
      return res.data;
    },
    enabled: !!jobId,
  });
};

// Queue
export const useQueue = () => {
  return useQuery<JobApplication[]>({
    queryKey: ["queue"],
    queryFn: async () => {
      const res = await apiClient.get<JobApplication[]>("/queue");
      return res.data;
    },
    refetchInterval: 2500,
  });
};

export const useExternalQueue = () => {
  return useQuery<JobApplication[]>({
    queryKey: ["queue-external"],
    queryFn: async () => {
      const res = await apiClient.get<JobApplication[]>("/queue/external");
      return res.data;
    },
    refetchInterval: 3000,
  });
};

// History
export const useHistory = (params?: { status?: string; search?: string }) => {
  return useQuery<JobApplication[]>({
    queryKey: ["history", params],
    queryFn: async () => {
      const res = await apiClient.get<JobApplication[]>("/history", { params });
      return res.data;
    },
  });
};

// Candidate Profile & Resumes
export const useProfile = () => {
  return useQuery<CandidateProfile>({
    queryKey: ["profile"],
    queryFn: async () => {
      const res = await apiClient.get<CandidateProfile>("/profile");
      return res.data;
    },
  });
};

export const useResumes = () => {
  return useQuery<ResumeVersion[]>({
    queryKey: ["resumes"],
    queryFn: async () => {
      const res = await apiClient.get<ResumeVersion[]>("/profile/resumes");
      return res.data;
    },
  });
};

// Settings & Preferences
export const useAutomationSettings = () => {
  return useQuery<AutomationSettings>({
    queryKey: ["settings-automation"],
    queryFn: async () => {
      const res = await apiClient.get<AutomationSettings>("/settings/automation");
      return res.data;
    },
  });
};

export const useJobPreferences = () => {
  return useQuery<JobPreferences>({
    queryKey: ["settings-preferences"],
    queryFn: async () => {
      const res = await apiClient.get<JobPreferences>("/settings/preferences");
      return res.data;
    },
  });
};

// Logs
export const useActivityLogs = (params?: { level?: string; search?: string }) => {
  return useQuery<ActivityLog[]>({
    queryKey: ["logs", params],
    queryFn: async () => {
      const res = await apiClient.get<ActivityLog[]>("/logs", { params });
      return res.data;
    },
    refetchInterval: 4000,
  });
};

// Mutations
export const useAppMutations = () => {
  const qc = useQueryClient();

  // Profile update
  const updateProfile = useMutation({
    mutationFn: async (data: Partial<CandidateProfile>) => {
      const res = await apiClient.put<CandidateProfile>("/profile", data);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["profile"] }),
  });

  // Resume upload
  const uploadResume = useMutation({
    mutationFn: async (formData: FormData) => {
      const res = await apiClient.post<ResumeVersion>("/profile/resumes/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["resumes"] }),
  });

  // Resume paste (LaTeX or Plain Text)
  const pasteResume = useMutation({
    mutationFn: async (payload: {
      label: string;
      target_categories: string[];
      is_primary: boolean;
      file_type: string;
      content: string;
    }) => {
      const res = await apiClient.post<ResumeVersion>("/profile/resumes/paste", payload);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["resumes"] }),
  });

  // Set primary resume
  const setPrimaryResume = useMutation({
    mutationFn: async (resumeId: number) => {
      await apiClient.put(`/profile/resumes/${resumeId}/primary`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["resumes"] }),
  });

  // Delete resume
  const deleteResume = useMutation({
    mutationFn: async (resumeId: number) => {
      await apiClient.delete(`/profile/resumes/${resumeId}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["resumes"] }),
  });

  // Discover jobs
  const discoverJobs = useMutation({
    mutationFn: async (source: string = "all") => {
      const res = await apiClient.post(`/jobs/discover?source=${source}`);
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  // Curate jobs by candidate resume
  const curateJobs = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post("/jobs/curate");
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  // Import job URL
  const importJobUrl = useMutation({
    mutationFn: async (jobData: any) => {
      const res = await apiClient.post("/jobs/import/url", jobData);
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  // Import CSV
  const importCsv = useMutation({
    mutationFn: async (file: File) => {
      const fd = new FormData();
      fd.append("file", file);
      const res = await apiClient.post("/jobs/import/csv", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  // Queue a job
  const queueJob = useMutation({
    mutationFn: async (jobId: number) => {
      const res = await apiClient.post(`/jobs/${jobId}/queue`);
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["queue"] });
      qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  // Automation session controls
  const startAutomation = useMutation({
    mutationFn: async (params?: { target?: number; delay?: number }) => {
      const res = await apiClient.post("/automation/start", params || {});
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["automation-status"] });
      qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  const pauseAutomation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post("/automation/pause");
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["automation-status"] }),
  });

  const resumeAutomation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post("/automation/resume");
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["automation-status"] }),
  });

  const stopAutomation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post("/automation/stop");
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["automation-status"] }),
  });

  const retryFailed = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post("/automation/retry-failed");
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["queue"] });
      qc.invalidateQueries({ queryKey: ["history"] });
      qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  const autoBuildQueue = useMutation({
    mutationFn: async (targetCount: number = 15) => {
      const res = await apiClient.post("/automation/build-queue", { target_count: targetCount });
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["queue"] });
      qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  // Queue actions
  const approveApplication = useMutation({
    mutationFn: async (appId: number) => {
      const res = await apiClient.put(`/queue/${appId}/approve`);
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["queue"] });
      qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  const skipApplication = useMutation({
    mutationFn: async (appId: number) => {
      const res = await apiClient.put(`/queue/${appId}/skip`);
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["queue"] });
      qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  const markManualApplied = useMutation({
    mutationFn: async ({ appId, notes }: { appId: number; notes?: string }) => {
      const res = await apiClient.put(`/queue/${appId}/manual-applied`, { notes });
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["queue-external"] });
      qc.invalidateQueries({ queryKey: ["history"] });
      qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  // Settings updates
  const updateAutomationSettings = useMutation({
    mutationFn: async (data: Partial<AutomationSettings>) => {
      const res = await apiClient.put("/settings/automation", data);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings-automation"] }),
  });

  const updateJobPreferences = useMutation({
    mutationFn: async (data: Partial<JobPreferences>) => {
      const res = await apiClient.put("/settings/preferences", data);
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings-preferences"] }),
  });

  // Demo seed
  const seedDemoData = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post("/settings/seed-demo");
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries();
    },
  });

  // Clear logs
  const clearLogs = useMutation({
    mutationFn: async () => {
      await apiClient.delete("/logs/clear");
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["logs"] }),
  });

  // Live Browser Bot Control & Direct Apply
  const applySingleJobInBrowser = useMutation({
    mutationFn: async (jobId: number) => {
      const res = await apiClient.post(`/automation/browser/apply-job/${jobId}`);
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["queue"] });
      qc.invalidateQueries({ queryKey: ["history"] });
      qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
      qc.invalidateQueries({ queryKey: ["automation-status"] });
    },
  });

  const applyCustomUrlInBrowser = useMutation({
    mutationFn: async ({ url, title, company }: { url: string; title?: string; company?: string }) => {
      const res = await apiClient.post("/automation/browser/apply-url", { url, title, company });
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["queue"] });
      qc.invalidateQueries({ queryKey: ["history"] });
      qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
      qc.invalidateQueries({ queryKey: ["automation-status"] });
    },
  });

  const launchDesktopBrowser = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post("/automation/browser/launch");
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["automation-status"] });
    },
  });

  const closeDesktopBrowser = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post("/automation/browser/close");
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["automation-status"] });
    },
  });

  const toggleSimulationMode = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post("/automation/toggle-simulation");
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["automation-status"] });
      qc.invalidateQueries({ queryKey: ["settings-automation"] });
      qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  const openPortalLogin = useMutation({
    mutationFn: async (site: string = "linkedin") => {
      const res = await apiClient.post(`/automation/browser/login?site=${site}`);
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["browser-sessions"] });
      qc.invalidateQueries({ queryKey: ["automation-status"] });
    },
  });

  const connectChromeCdp = useMutation({
    mutationFn: async (cdpUrl: string = "http://127.0.0.1:9222") => {
      const res = await apiClient.post(`/automation/browser/connect-cdp?cdp_url=${encodeURIComponent(cdpUrl)}`);
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["browser-sessions"] });
      qc.invalidateQueries({ queryKey: ["automation-status"] });
    },
  });

  const applyMultiTabInBrowser = useMutation({
    mutationFn: async ({
      urls,
      delaySeconds = 3,
      autoSubmit = true,
    }: {
      urls: string[];
      delaySeconds?: number;
      autoSubmit?: boolean;
    }) => {
      const res = await apiClient.post("/automation/browser/apply-multi-tab", {
        urls,
        delay_seconds: delaySeconds,
        auto_submit: autoSubmit,
      });
      return res.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["queue"] });
      qc.invalidateQueries({ queryKey: ["history"] });
      qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
      qc.invalidateQueries({ queryKey: ["automation-status"] });
    },
  });

  return {
    updateProfile,
    uploadResume,
    pasteResume,
    setPrimaryResume,
    deleteResume,
    discoverJobs,
    curateJobs,
    importJobUrl,
    importCsv,
    queueJob,
    startAutomation,
    pauseAutomation,
    resumeAutomation,
    stopAutomation,
    retryFailed,
    autoBuildQueue,
    approveApplication,
    skipApplication,
    markManualApplied,
    updateAutomationSettings,
    updateJobPreferences,
    seedDemoData,
    clearLogs,
    applySingleJobInBrowser,
    applyCustomUrlInBrowser,
    launchDesktopBrowser,
    closeDesktopBrowser,
    toggleSimulationMode,
    openPortalLogin,
    connectChromeCdp,
    applyMultiTabInBrowser,
  };
};
