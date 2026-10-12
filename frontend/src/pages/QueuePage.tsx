import React, { useState } from "react";
import {
  ListOrdered,
  ExternalLink,
  CheckCircle2,
  XCircle,
  Copy,
  Check,
  FileText,
  AlertTriangle,
  Play,
  RotateCcw,
  Sparkles,
  Info,
} from "lucide-react";
import { useQueue, useExternalQueue, useAppMutations, useAutomationStatus } from "../api/hooks";
import { JobApplication } from "../types";
import { ReviewModal } from "../components/queue/ReviewModal";

export const QueuePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"active" | "external">("active");
  const { data: queue = [], isLoading: loadingActive } = useQueue();
  const { data: extQueue = [], isLoading: loadingExt } = useExternalQueue();
  const { data: status } = useAutomationStatus();

  const {
    startAutomation,
    pauseAutomation,
    resumeAutomation,
    stopAutomation,
    autoBuildQueue,
    skipApplication,
    approveApplication,
    markManualApplied,
  } = useAppMutations();

  const [reviewApp, setReviewApp] = useState<JobApplication | null>(null);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [manualNotesInput, setManualNotesInput] = useState<{ [id: number]: string }>({});

  const handleCopyCandidateInfo = (app: JobApplication) => {
    const prep = app.prepared_data || {};
    const text = `Full Name: ${prep.full_name || ""}\nEmail: ${prep.email || ""}\nPhone: ${prep.phone || ""}\nPortfolio: ${prep.portfolio_url || ""}\nGitHub: ${prep.github_url || ""}\nLinkedIn: ${prep.linkedin_url || ""}`;
    navigator.clipboard.writeText(text);
    setCopiedId(app.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleCopyCoverLetter = (app: JobApplication) => {
    navigator.clipboard.writeText(app.cover_letter || "");
    setCopiedId(app.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const isRunning = status?.is_active && !status?.is_paused;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Application Queue</h1>
          <p className="text-xs md:text-sm text-text-muted mt-0.5">
            Manage pending submissions, human review checkpoints, and manual external workflows.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => autoBuildQueue.mutate(15)}
            disabled={autoBuildQueue.isPending}
            className="fluent-button fluent-button-secondary text-xs"
            title="Automatically queue top matching jobs from database"
          >
            <Sparkles className="w-3.5 h-3.5 text-primary" />
            <span>Auto-Build Queue (15)</span>
          </button>

          {!status?.is_active ? (
            <button
              onClick={() => startAutomation.mutate({ target: 15, delay: 2.0 })}
              className="fluent-button fluent-button-primary text-xs"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Start Session</span>
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-xs text-text-muted">
                Processing {status.submitted_count}/{status.target_count}
              </span>
              <button
                onClick={() => stopAutomation.mutate()}
                className="fluent-button fluent-button-secondary text-xs text-danger"
              >
                Stop
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-border">
        <button
          onClick={() => setActiveTab("active")}
          className={`flex items-center gap-2 pb-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "active"
              ? "border-primary text-primary"
              : "border-transparent text-text-secondary hover:text-text-primary"
          }`}
        >
          <ListOrdered className="w-4 h-4" />
          <span>Active Pipeline ({queue.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("external")}
          className={`flex items-center gap-2 pb-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "external"
              ? "border-primary text-primary"
              : "border-transparent text-text-secondary hover:text-text-primary"
          }`}
        >
          <ExternalLink className="w-4 h-4" />
          <span>External Manual Queue ({extQueue.length})</span>
        </button>
      </div>

      {/* Tab 1: Active Application Queue */}
      {activeTab === "active" && (
        <div className="space-y-4">
          {loadingActive ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="fluent-card p-4 h-20 animate-pulse bg-surfaceHover/30" />
              ))}
            </div>
          ) : queue.length === 0 ? (
            <div className="fluent-card p-12 text-center">
              <ListOrdered className="w-12 h-12 mx-auto text-text-muted mb-3 opacity-50" />
              <h3 className="text-base font-semibold text-text-primary">Queue is empty</h3>
              <p className="text-xs text-text-muted mt-1 max-w-sm mx-auto">
                No applications currently queued. Use "Auto-Build Queue" or add jobs from the Find Jobs page.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {queue.map((app, index) => {
                const job = app.job;
                const isCurrent = status?.current_job_id === app.job_id;

                return (
                  <div
                    key={app.id}
                    className={`fluent-card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all ${
                      isCurrent ? "border-primary/60 bg-primary/5" : ""
                    }`}
                  >
                    <div className="flex items-start sm:items-center gap-3">
                      <span className="w-6 h-6 rounded-md bg-surfaceHover text-text-muted text-xs font-bold flex items-center justify-center shrink-0">
                        #{index + 1}
                      </span>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-sm font-semibold text-text-primary">{job?.title}</h4>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              app.status === "AWAITING_REVIEW"
                                ? "bg-warning/15 text-warning"
                                : app.status === "READY_TO_SUBMIT"
                                ? "bg-success/15 text-success"
                                : app.status === "PREPARING"
                                ? "bg-primary/15 text-primary"
                                : "bg-surfaceHover text-text-muted"
                            }`}
                          >
                            {app.status}
                          </span>
                        </div>
                        <p className="text-xs text-text-muted mt-0.5">
                          {job?.company} • Match: <span className="font-semibold text-text-primary">{job?.match_score}%</span> • Method: {job?.application_method}
                        </p>
                        <p className="text-[11px] text-text-secondary mt-1">
                          Last Action: {app.last_action}
                        </p>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 self-end sm:self-center">
                      <button
                        onClick={() => setReviewApp(app)}
                        className="fluent-button fluent-button-secondary text-xs py-1.5 px-3"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>Inspect & Review</span>
                      </button>

                      {app.status === "AWAITING_REVIEW" && (
                        <button
                          onClick={() => approveApplication.mutate(app.id)}
                          className="fluent-button fluent-button-primary text-xs py-1.5 px-3"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Approve</span>
                        </button>
                      )}

                      <button
                        onClick={() => skipApplication.mutate(app.id)}
                        className="p-1.5 text-text-muted hover:text-danger rounded-md hover:bg-surfaceHover transition-colors"
                        title="Skip application"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: External Application Queue (Manual Assistance) */}
      {activeTab === "external" && (
        <div className="space-y-4">
          <div className="p-3.5 rounded-xl bg-primary/10 border border-primary/20 flex items-start gap-3">
            <Info className="w-4 h-4 text-primary shrink-0 mt-0.5" />
            <p className="text-xs text-text-secondary leading-relaxed">
              These jobs require external application portals (such as LinkedIn, Wellfound, or proprietary corporate career sites) where direct automation is restricted or unsupported. ApplyPilot has prepared your truthful candidate information and customized cover letter so you can complete them in seconds.
            </p>
          </div>

          {loadingExt ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="fluent-card p-5 h-32 animate-pulse bg-surfaceHover/30" />
              ))}
            </div>
          ) : extQueue.length === 0 ? (
            <div className="fluent-card p-12 text-center">
              <ExternalLink className="w-12 h-12 mx-auto text-text-muted mb-3 opacity-50" />
              <h3 className="text-base font-semibold text-text-primary">No manual actions required</h3>
              <p className="text-xs text-text-muted mt-1 max-w-sm mx-auto">
                Applications routed for external manual submission will appear here.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {extQueue.map((app) => {
                const job = app.job;
                const notes = manualNotesInput[app.id] ?? app.manual_notes;

                return (
                  <div key={app.id} className="fluent-card p-5 space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-text-primary text-base">{job?.title}</h3>
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-primary/15 text-primary">
                            {job?.source_platform}
                          </span>
                        </div>
                        <p className="text-xs text-text-muted mt-0.5">{job?.company} • Match Score: {job?.match_score}%</p>
                      </div>

                      <div className="flex items-center gap-2">
                        {job?.original_url && (
                          <a
                            href={job.original_url}
                            target="_blank"
                            rel="noreferrer"
                            className="fluent-button fluent-button-primary text-xs py-1.5 px-3"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                            <span>Open Application Page</span>
                          </a>
                        )}
                      </div>
                    </div>

                    {/* Quick Copy Helpers */}
                    <div className="p-3 bg-surfaceHover/50 rounded-lg border border-border flex flex-wrap items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleCopyCandidateInfo(app)}
                          className="fluent-button fluent-button-secondary text-xs py-1 px-2.5"
                        >
                          <Copy className="w-3 h-3" />
                          <span>{copiedId === app.id ? "Copied!" : "Copy Candidate Info"}</span>
                        </button>

                        <button
                          onClick={() => handleCopyCoverLetter(app)}
                          className="fluent-button fluent-button-secondary text-xs py-1 px-2.5"
                        >
                          <Copy className="w-3 h-3" />
                          <span>{copiedId === app.id ? "Copied!" : "Copy Cover Letter"}</span>
                        </button>
                      </div>

                      <span className="text-[11px] text-text-muted">
                        Selected Resume: <span className="text-text-primary font-medium">{app.resume?.label || "Default Resume"}</span>
                      </span>
                    </div>

                    {/* User Confirmation & Notes */}
                    <div className="pt-2 flex flex-col sm:flex-row items-center gap-3">
                      <input
                        type="text"
                        placeholder="Add optional notes (e.g. Applied via LinkedIn, Confirmation #1234)..."
                        value={notes}
                        onChange={(e) =>
                          setManualNotesInput({ ...manualNotesInput, [app.id]: e.target.value })
                        }
                        className="fluent-input flex-1 text-xs w-full"
                      />

                      <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                        <button
                          onClick={() => skipApplication.mutate(app.id)}
                          className="fluent-button fluent-button-secondary text-xs py-1.5 px-3 text-danger hover:border-danger/40"
                        >
                          Skip
                        </button>

                        <button
                          onClick={() =>
                            markManualApplied.mutate({
                              appId: app.id,
                              notes: notes || undefined,
                            })
                          }
                          disabled={markManualApplied.isPending}
                          className="fluent-button fluent-button-primary text-xs py-1.5 px-4"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Mark as Applied</span>
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Review Modal */}
      <ReviewModal app={reviewApp} onClose={() => setReviewApp(null)} />
    </div>
  );
};
