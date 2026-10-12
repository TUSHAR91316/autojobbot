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

  const { data: jobs = [], isLoading } = useJobs({
    search: search || undefined,
    company: company || undefined,
    work_mode: workMode !== "all" ? workMode : undefined,
    source_platform: source !== "all" ? source : undefined,
    min_score: minScore > 0 ? minScore : undefined,
    status: statusFilter !== "all" ? statusFilter : undefined,
  });

  const { discoverJobs, queueJob } = useAppMutations();

  return (
    <div className="space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Discover & Search Jobs</h1>
          <p className="text-xs md:text-sm text-text-muted mt-0.5">
            Unified listings across permitted public feeds, direct CSV imports, and user-provided jobs.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => discoverJobs.mutate("all")}
            disabled={discoverJobs.isPending}
            className="fluent-button fluent-button-primary text-xs"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{discoverJobs.isPending ? "Discovering..." : "Discover New Jobs"}</span>
          </button>

          <button
            onClick={() => setIsImportModalOpen(true)}
            className="fluent-button fluent-button-secondary text-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Import Job (URL/CSV)</span>
          </button>

          <a
            href={`${API_BASE_URL}/jobs/export/csv`}
            download="applypilot_jobs.csv"
            className="fluent-button fluent-button-secondary text-xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </a>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="fluent-card p-4 space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          {/* Keyword Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted" />
            <input
              type="text"
              placeholder="Filter by title or skills..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="fluent-input w-full pl-8 text-xs"
            />
          </div>

          {/* Company */}
          <div>
            <input
              type="text"
              placeholder="Filter by company..."
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="fluent-input w-full text-xs"
            />
          </div>

          {/* Work Mode */}
          <div>
            <select
              value={workMode}
              onChange={(e) => setWorkMode(e.target.value)}
              className="fluent-input w-full text-xs"
            >
              <option value="all">All Work Modes</option>
              <option value="remote">Remote Only</option>
              <option value="hybrid">Hybrid</option>
              <option value="onsite">Onsite</option>
            </select>
          </div>

          {/* Source Platform */}
          <div>
            <select
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="fluent-input w-full text-xs"
            >
              <option value="all">All Sources</option>
              <option value="remoteok">RemoteOK</option>
              <option value="jobicy">Jobicy</option>
              <option value="synthetic_demo">Synthetic Demo</option>
              <option value="manual">Manual / URL</option>
              <option value="csv_import">CSV Import</option>
            </select>
          </div>
        </div>

        {/* Second Filter Row */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-1 border-t border-border/50 text-xs">
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
            Try adjusting your search filters or click "Discover New Jobs" to fetch from authorized public feeds.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {jobs.map((job) => {
            const elig = job.eligibility_assessment || { is_eligible: true, reasons: [] };
            const isEligible = elig.is_eligible;

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

                    {/* Match Score Badge (Clickable) */}
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
                        <DollarSign className="w-3 h-3 text-success" />
                        <span>
                          {job.salary_min ? `$${job.salary_min.toLocaleString()}` : ""}
                          {job.salary_min && job.salary_max ? " - " : ""}
                          {job.salary_max ? `$${job.salary_max.toLocaleString()}` : ""}
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
                <div className="pt-4 mt-4 border-t border-border flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-text-muted capitalize">
                      Source: {job.source_platform}
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

                  <button
                    onClick={() => queueJob.mutate(job.id)}
                    disabled={job.status === "QUEUED" || job.status === "APPLIED" || queueJob.isPending}
                    className={`fluent-button text-xs py-1.5 px-3 ${
                      job.status === "QUEUED" || job.status === "APPLIED"
                        ? "bg-surfaceHover text-text-muted cursor-not-allowed"
                        : "fluent-button-primary"
                    }`}
                  >
                    {job.status === "QUEUED" ? (
                      <span className="flex items-center gap-1">
                        <Check className="w-3 h-3 text-primary" /> In Queue
                      </span>
                    ) : job.status === "APPLIED" ? (
                      <span>Applied</span>
                    ) : (
                      <span>Add to Queue</span>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modals */}
      <ScoreBreakdownModal job={selectedJobForModal} onClose={() => setSelectedJobForModal(null)} />
      <JobImportModal isOpen={isImportModalOpen} onClose={() => setIsImportModalOpen(false)} />
    </div>
  );
};
