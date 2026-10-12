import React, { useState } from "react";
import {
  Search,
  Filter,
  Plus,
  Download,
  Sparkles,
  ExternalLink,
  Check,
  AlertCircle,
  HelpCircle,
  Building,
  MapPin,
  DollarSign,
  Briefcase,
  Globe,
  Play,
  CheckCircle2,
  X,
  Eye,
  Loader2,
} from "lucide-react";
import { useJobs, useAppMutations } from "../api/hooks";
import { JobListing } from "../types";
import { ScoreBreakdownModal } from "../components/jobs/ScoreBreakdownModal";
import { JobImportModal } from "../components/jobs/JobImportModal";
import { API_BASE_URL } from "../api/client";

export const FindJobsPage: React.FC = () => {
  const [search, setSearch] = useState("");
  const [company, setCompany] = useState("");
  const [workMode, setWorkMode] = useState("all");
  const [source, setSource] = useState("all");
  const [minScore, setMinScore] = useState<number>(0);
  const [statusFilter, setStatusFilter] = useState("all");

  const [selectedJobForModal, setSelectedJobForModal] = useState<JobListing | null>(null);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);

  // Quick Direct URL input state
  const [quickUrl, setQuickUrl] = useState("");
  const [applyingJobId, setApplyingJobId] = useState<number | null>(null);
  const [browserResultModal, setBrowserResultModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    outcome: string;
    steps: string[];
    screenshot?: string;
  } | null>(null);

  const { data: jobs = [], isLoading } = useJobs({
    search: search || undefined,
    company: company || undefined,
    work_mode: workMode !== "all" ? workMode : undefined,
    source_platform: source !== "all" ? source : undefined,
    min_score: minScore > 0 ? minScore : undefined,
    status: statusFilter !== "all" ? statusFilter : undefined,
  });

  const {
    discoverJobs,
    queueJob,
    applySingleJobInBrowser,
    applyCustomUrlInBrowser,
  } = useAppMutations();

  const handleApplySingleJob = async (job: JobListing) => {
    try {
      setApplyingJobId(job.id);
      const res = await applySingleJobInBrowser.mutateAsync(job.id);
      setBrowserResultModal({
        isOpen: true,
        title: `${job.title} at ${job.company}`,
        message: res.message || "Browser automation workflow completed.",
        outcome: res.outcome || "SUBMITTED",
        steps: res.steps_completed || [],
        screenshot: res.screenshot,
      });
    } catch (err: any) {
      setBrowserResultModal({
        isOpen: true,
        title: `${job.title} at ${job.company}`,
        message: err.response?.data?.detail || err.message || "Browser automation failed.",
        outcome: "FAILED",
        steps: [],
      });
    } finally {
      setApplyingJobId(null);
    }
  };

  const handleQuickUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickUrl.trim()) return;

    try {
      setApplyingJobId(-1);
      const res = await applyCustomUrlInBrowser.mutateAsync({
        url: quickUrl.trim(),
        title: "Direct Job Application",
        company: "Direct Employer",
      });
      setBrowserResultModal({
        isOpen: true,
        title: "Direct URL Browser Application",
        message: res.message || "Browser finished filling application fields.",
        outcome: res.outcome || "SUBMITTED",
        steps: res.steps_completed || [],
        screenshot: res.screenshot,
      });
      setQuickUrl("");
    } catch (err: any) {
      setBrowserResultModal({
        isOpen: true,
        title: "Direct URL Browser Application",
        message: err.response?.data?.detail || err.message || "Failed to launch browser.",
        outcome: "FAILED",
        steps: [],
      });
    } finally {
      setApplyingJobId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Discover & Apply to Jobs</h1>
          <p className="text-xs md:text-sm text-text-muted mt-0.5">
            Evaluate match eligibility, queue verified listings, or command our <strong>Live Desktop Browser Bot</strong> to apply directly for you.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setIsImportModalOpen(true)}
            className="fluent-button fluent-button-secondary text-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Import Job / CSV</span>
          </button>

          <a
            href={`${API_BASE_URL}/jobs/export/csv`}
            download="applypilot_jobs.csv"
            className="fluent-button fluent-button-secondary text-xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </a>

          <button
            onClick={() => discoverJobs.mutate("all")}
            disabled={discoverJobs.isPending}
            className="fluent-button fluent-button-primary text-xs"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{discoverJobs.isPending ? "Searching Feeds..." : "Discover New Jobs"}</span>
          </button>
        </div>
      </div>

      {/* QUICK BROWSER APPLY TOOLBAR */}
      <div className="fluent-card p-4 bg-gradient-to-r from-primary/10 via-surface to-surface border-primary/30 shadow-sm">
        <form onSubmit={handleQuickUrlSubmit} className="flex flex-col md:flex-row items-stretch md:items-center gap-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-text-primary shrink-0">
            <Globe className="w-4 h-4 text-primary animate-pulse" />
            <span>Browser Bot Quick Apply:</span>
          </div>

          <div className="relative flex-1">
            <input
              type="url"
              placeholder="Paste ANY job link (LinkedIn, Greenhouse, Lever, Indeed, Company Site)..."
              value={quickUrl}
              onChange={(e) => setQuickUrl(e.target.value)}
              className="fluent-input w-full text-xs pr-10"
            />
          </div>

          <button
            type="submit"
            disabled={applyCustomUrlInBrowser.isPending || !quickUrl.trim()}
            className="fluent-button fluent-button-primary text-xs py-2 px-4 shrink-0 flex items-center justify-center gap-1.5 shadow-sm"
          >
            {applyCustomUrlInBrowser.isPending ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Launching Browser...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Apply with Browser Bot</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="fluent-card p-4 space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search by title or keyword..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="fluent-input w-full pl-9 text-xs"
            />
          </div>

          <div>
            <input
              type="text"
              placeholder="Filter by company..."
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="fluent-input w-full text-xs"
            />
          </div>

          <div>
            <select
              value={workMode}
              onChange={(e) => setWorkMode(e.target.value)}
              className="fluent-input w-full text-xs"
            >
              <option value="all">Work Mode: All</option>
              <option value="remote">Remote Only</option>
              <option value="hybrid">Hybrid</option>
              <option value="onsite">On-site</option>
            </select>
          </div>

          <div>
            <select
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="fluent-input w-full text-xs"
            >
              <option value="all">Source: All Platforms</option>
              <option value="remoteok">RemoteOK</option>
              <option value="jobicy">Jobicy</option>
              <option value="manual">Manual / Direct</option>
              <option value="csv_import">CSV Import</option>
            </select>
          </div>
        </div>

        {/* Second Row: Sliders & Status Pill Filters */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-border text-xs">
          <div className="flex items-center gap-3">
            <span className="text-text-muted">Min Match Score:</span>
            <input
              type="range"
              min="0"
              max="90"
              step="5"
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="w-32 accent-primary"
            />
            <span className="font-semibold text-text-primary">{minScore}%</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-text-muted">Status:</span>
            {["all", "DISCOVERED", "MATCHED", "QUEUED", "APPLIED"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                  statusFilter === st
                    ? "bg-primary text-slate-900 font-semibold"
                    : "bg-surfaceHover text-text-secondary hover:text-text-primary"
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Listings Count */}
      <div className="flex items-center justify-between text-xs text-text-muted px-1">
        <span>Showing {jobs.length} jobs</span>
      </div>

      {/* Job Cards Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="fluent-card p-5 h-44 animate-pulse bg-surfaceHover/30" />
          ))}
        </div>
      ) : jobs.length === 0 ? (
        <div className="fluent-card p-12 text-center">
          <Building className="w-12 h-12 mx-auto text-text-muted mb-3 opacity-50" />
          <h3 className="text-base font-semibold text-text-primary">No matching jobs found</h3>
          <p className="text-xs text-text-muted mt-1 max-w-sm mx-auto">
            Try adjusting your search filters or click "Discover New Jobs" to fetch from authorized feeds.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {jobs.map((job) => {
            const elig = job.eligibility_assessment || { is_eligible: true, reasons: [] };
            const isEligible = elig.is_eligible;
            const isApplyingThis = applyingJobId === job.id;

            return (
              <div
                key={job.id}
                className="fluent-card p-5 flex flex-col justify-between hover:border-borderHover transition-all"
              >
                <div>
                  {/* Top Bar of Card */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-0.5">
                      <h3 className="font-semibold text-text-primary text-sm line-clamp-1">{job.title}</h3>
                      <div className="text-xs text-text-secondary font-medium">{job.company}</div>
                    </div>

                    {/* Match Score Badge */}
                    <button
                      onClick={() => setSelectedJobForModal(job)}
                      className={`px-2 py-1 rounded-md text-xs font-bold border transition-colors flex items-center gap-1 ${
                        job.match_score >= 75
                          ? "bg-success/10 border-success/30 text-success hover:bg-success/20"
                          : job.match_score >= 50
                          ? "bg-warning/10 border-warning/30 text-warning hover:bg-warning/20"
                          : "bg-danger/10 border-danger/30 text-danger hover:bg-danger/20"
                      }`}
                      title="Click to view weighted score breakdown"
                    >
                      <span>{job.match_score}% Match</span>
                      <HelpCircle className="w-3 h-3 opacity-70" />
                    </button>
                  </div>

                  {/* Metadata Chips */}
                  <div className="flex flex-wrap items-center gap-3 text-xs text-text-muted mt-3">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-text-muted" />
                      <span>{job.location || "Remote"}</span>
                    </span>
                    <span className="flex items-center gap-1">
                      <Briefcase className="w-3 h-3 text-text-muted" />
                      <span className="capitalize">{job.work_mode}</span>
                    </span>
                    {(job.salary_min || job.salary_max) && (
                      <span className="flex items-center gap-1 text-text-primary">
                        <span className="text-success font-bold text-xs">{job.salary_currency === "INR" ? "₹" : "$"}</span>
                        <span>
                          {job.salary_currency === "INR" ? (
                            <>
                              {job.salary_min ? `₹${(job.salary_min / 100000).toFixed(1)}L` : ""}
                              {job.salary_min && job.salary_max ? " - " : ""}
                              {job.salary_max ? `₹${(job.salary_max / 100000).toFixed(1)}L PA` : ""}
                            </>
                          ) : (
                            <>
                              {job.salary_min ? `$${job.salary_min.toLocaleString()}` : ""}
                              {job.salary_min && job.salary_max ? " - " : ""}
                              {job.salary_max ? `$${job.salary_max.toLocaleString()}` : ""}
                            </>
                          )}
                        </span>
                      </span>
                    )}
                  </div>

                  {/* Required Skills */}
                  {job.required_skills && job.required_skills.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {job.required_skills.slice(0, 5).map((skill, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded text-[10px] bg-surfaceHover text-text-secondary font-medium"
                        >
                          {skill}
                        </span>
                      ))}
                      {job.required_skills.length > 5 && (
                        <span className="text-[10px] text-text-muted self-center">
                          +{job.required_skills.length - 5} more
                        </span>
                      )}
                    </div>
                  )}

                  {/* Ineligibility Warning if flagged */}
                  {!isEligible && (
                    <div className="mt-3 p-2 rounded bg-danger/10 border border-danger/20 flex items-center gap-1.5 text-[11px] text-danger">
                      <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                      <span className="truncate">
                        {elig.reasons?.[0] || "Requirements do not meet profile"}
                      </span>
                    </div>
                  )}
                </div>

                {/* Footer Actions */}
                <div className="pt-4 mt-4 border-t border-border flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-text-muted capitalize">
                      {job.source_platform}
                    </span>
                    {job.original_url && (
                      <a
                        href={job.original_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-text-muted hover:text-text-primary"
                        title="Open posting"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>

                  <div className="flex items-center gap-1.5">
                    {/* Direct Live Browser Apply Button */}
                    <button
                      onClick={() => handleApplySingleJob(job)}
                      disabled={isApplyingThis || job.status === "APPLIED"}
                      className={`fluent-button text-xs py-1.5 px-2.5 font-semibold flex items-center gap-1 ${
                        job.status === "APPLIED"
                          ? "bg-surfaceHover text-text-muted cursor-not-allowed"
                          : "bg-primary text-slate-900 hover:bg-primaryHover"
                      }`}
                      title="Launch visible desktop browser and apply immediately"
                    >
                      {isApplyingThis ? (
                        <>
                          <Loader2 className="w-3 h-3 animate-spin" />
                          <span>Applying...</span>
                        </>
                      ) : job.status === "APPLIED" ? (
                        <>
                          <Check className="w-3 h-3 text-success" />
                          <span>Applied</span>
                        </>
                      ) : (
                        <>
                          <Play className="w-3 h-3 fill-current" />
                          <span>Apply in Browser</span>
                        </>
                      )}
                    </button>

                    {/* Standard Queue Button */}
                    <button
                      onClick={() => queueJob.mutate(job.id)}
                      disabled={job.status === "QUEUED" || job.status === "APPLIED" || queueJob.isPending}
                      className={`fluent-button text-xs py-1.5 px-2.5 ${
                        job.status === "QUEUED" || job.status === "APPLIED"
                          ? "bg-surfaceHover text-text-muted cursor-not-allowed"
                          : "fluent-button-secondary"
                      }`}
                    >
                      {job.status === "QUEUED" ? (
                        <span className="flex items-center gap-1">
                          <Check className="w-3 h-3 text-primary" /> In Queue
                        </span>
                      ) : job.status === "APPLIED" ? (
                        <span>Done</span>
                      ) : (
                        <span>Queue</span>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Browser Result Modal */}
      {browserResultModal && browserResultModal.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="fluent-card w-full max-w-xl bg-surface border-border p-6 shadow-2xl relative space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-primary" />
                <h3 className="font-semibold text-text-primary text-sm">Browser Bot Report</h3>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    browserResultModal.outcome === "SUBMITTED"
                      ? "bg-success/20 text-success"
                      : browserResultModal.outcome === "PARTIAL_FILLED" || browserResultModal.outcome === "MANUAL_ACTION_REQUIRED"
                      ? "bg-warning/20 text-warning"
                      : "bg-danger/20 text-danger"
                  }`}
                >
                  {browserResultModal.outcome}
                </span>
              </div>
              <button
                onClick={() => setBrowserResultModal(null)}
                className="p-1 text-text-muted hover:text-text-primary rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <h4 className="text-xs font-semibold text-text-primary">{browserResultModal.title}</h4>
              <p className="text-xs text-text-secondary mt-1">{browserResultModal.message}</p>
            </div>

            {browserResultModal.steps.length > 0 && (
              <div className="p-3 bg-surfaceHover/50 rounded-lg border border-border space-y-1.5">
                <span className="text-[11px] font-semibold text-text-primary block">Completed Automated Steps:</span>
                <div className="flex flex-wrap gap-1.5">
                  {browserResultModal.steps.map((step, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded text-[10px] bg-primary/10 text-primary font-mono flex items-center gap-1"
                    >
                      <CheckCircle2 className="w-3 h-3 text-success" />
                      <span>{step}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {browserResultModal.screenshot && (
              <div className="space-y-1 text-xs">
                <span className="font-medium text-text-secondary">Browser Screenshot:</span>
                <div className="rounded-lg border border-border overflow-hidden max-h-56 bg-slate-950 flex flex-col items-center justify-center">
                  {browserResultModal.screenshot.startsWith("/screenshots") ? (
                    <img
                      src={`http://127.0.0.1:8000${browserResultModal.screenshot}`}
                      alt="Application Screenshot"
                      className="w-full max-h-52 object-contain"
                    />
                  ) : (
                    <p className="text-[11px] text-text-muted p-2 truncate">
                      Saved locally at: <code className="text-primary">{browserResultModal.screenshot}</code>
                    </p>
                  )}
                </div>
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setBrowserResultModal(null)}
                className="fluent-button fluent-button-primary text-xs px-4 py-1.5"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modals */}
      <ScoreBreakdownModal job={selectedJobForModal} onClose={() => setSelectedJobForModal(null)} />
      <JobImportModal isOpen={isImportModalOpen} onClose={() => setIsImportModalOpen(false)} />
    </div>
  );
};
