import React from "react";
import {
  Compass,
  CheckCircle,
  Clock,
  ExternalLink,
  XCircle,
  FileCheck,
  TrendingUp,
  Activity,
  Play,
  Pause,
  Square,
  Sparkles,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";
import { useDashboardStats, useAppMutations } from "../api/hooks";
import { Link } from "react-router-dom";

export const DashboardPage: React.FC = () => {
  const { data: stats, isLoading } = useDashboardStats();
  const { startAutomation, pauseAutomation, resumeAutomation, stopAutomation, seedDemoData } = useAppMutations();

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-surfaceHover/50 w-64 rounded-md" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 bg-surfaceHover/40 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  const p = stats?.session_progress;
  const isRunning = p?.is_active && !p?.is_paused;
  const isPaused = p?.is_paused;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Overview Dashboard</h1>
          <p className="text-xs md:text-sm text-text-muted mt-0.5">
            Real-time pipeline metrics, local application telemetry, and session progress.
          </p>
        </div>

        {/* Quick Session Controls */}
        <div className="flex items-center gap-2">
          {!p?.is_active ? (
            <button
              onClick={() => startAutomation.mutate({ target: 15, delay: 2.0 })}
              disabled={startAutomation.isPending}
              className="fluent-button fluent-button-primary text-xs"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Start Session (Target: 15)</span>
            </button>
          ) : (
            <div className="flex items-center gap-2">
              {isRunning && (
                <button
                  onClick={() => pauseAutomation.mutate()}
                  className="fluent-button fluent-button-secondary text-xs text-warning"
                >
                  <Pause className="w-3.5 h-3.5" />
                  <span>Pause</span>
                </button>
              )}
              {isPaused && (
                <button
                  onClick={() => resumeAutomation.mutate()}
                  className="fluent-button fluent-button-secondary text-xs text-success"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Resume</span>
                </button>
              )}
              <button
                onClick={() => stopAutomation.mutate()}
                className="fluent-button fluent-button-secondary text-xs text-danger"
              >
                <Square className="w-3.5 h-3.5" />
                <span>Stop</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Zero State / Demo Seed Banner */}
      {stats?.jobs_discovered === 0 && (
        <div className="fluent-card p-5 border-primary/30 bg-primary/5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center shrink-0">
              <Sparkles className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-text-primary">Welcome to ApplyPilot!</h3>
              <p className="text-xs text-text-muted">
                Your local database is fresh and empty. You can discover permitted public feeds or seed realistic demo data to explore features.
              </p>
            </div>
          </div>
          <button
            onClick={() => seedDemoData.mutate()}
            disabled={seedDemoData.isPending}
            className="fluent-button fluent-button-primary text-xs shrink-0"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Load Demo Data</span>
          </button>
        </div>
      )}

      {/* Key Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Discovered */}
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-text-muted">Jobs Discovered</span>
            <Compass className="w-4 h-4 text-primary" />
          </div>
          <div className="text-2xl font-bold text-text-primary mt-2">{stats?.jobs_discovered || 0}</div>
          <div className="text-[11px] text-text-muted mt-1">
            Matching preference: <span className="font-semibold text-text-primary">{stats?.jobs_matching_preferences || 0}</span>
          </div>
        </div>

        {/* Submitted */}
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-text-muted">Applications Submitted</span>
            <CheckCircle className="w-4 h-4 text-success" />
          </div>
          <div className="text-2xl font-bold text-success mt-2">{stats?.applications_submitted || 0}</div>
          <div className="text-[11px] text-text-muted mt-1">Verified local submissions</div>
        </div>

        {/* Awaiting Review */}
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-text-muted">Awaiting Review</span>
            <Clock className="w-4 h-4 text-warning" />
          </div>
          <div className="text-2xl font-bold text-warning mt-2">{stats?.applications_awaiting_review || 0}</div>
          <div className="text-[11px] text-text-muted mt-1">Requires human check</div>
        </div>

        {/* External Manual Action */}
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-text-muted">Manual Action Queue</span>
            <ExternalLink className="w-4 h-4 text-primary" />
          </div>
          <div className="text-2xl font-bold text-text-primary mt-2">
            {stats?.external_manual_action_required || 0}
          </div>
          <div className="text-[11px] text-text-muted mt-1">Restricted or external sites</div>
        </div>
      </div>

      {/* Active Session Telemetry Box */}
      <div className="fluent-card p-5 border-border">
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary" />
            <h2 className="text-sm font-semibold text-text-primary">Current Automation Telemetry</h2>
          </div>
          <span
            className={`px-2 py-0.5 rounded text-[11px] font-semibold uppercase ${
              isRunning
                ? "bg-success/15 text-success"
                : isPaused
                ? "bg-warning/15 text-warning"
                : "bg-surfaceHover text-text-muted"
            }`}
          >
            {p?.status || "IDLE"}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-4 text-xs">
          <div>
            <span className="text-text-muted block">Session Target</span>
            <span className="text-base font-semibold text-text-primary">{p?.target_count || 15} apps</span>
          </div>
          <div>
            <span className="text-text-muted block">Processed So Far</span>
            <span className="text-base font-semibold text-text-primary">{p?.processed_count || 0}</span>
          </div>
          <div>
            <span className="text-text-muted block">Submitted</span>
            <span className="text-base font-semibold text-success">{p?.submitted_count || 0}</span>
          </div>
          <div>
            <span className="text-text-muted block">Manual Routed</span>
            <span className="text-base font-semibold text-primary">{p?.manual_count || 0}</span>
          </div>
        </div>

        {/* Current Action Banner */}
        <div className="mt-2 p-2.5 rounded-lg bg-surfaceHover/50 border border-border/70 flex items-center justify-between text-xs">
          <span className="text-text-secondary">
            Current Action: <span className="text-text-primary font-medium">{p?.current_action || "Idle. Ready to start session."}</span>
          </span>
          {p?.current_job_title && (
            <span className="text-primary font-medium truncate max-w-xs">{p.current_job_title}</span>
          )}
        </div>
      </div>

      {/* Two-Column Layout: Status Distribution & Sources */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Status Distribution */}
        <div className="fluent-card p-5">
          <h3 className="text-sm font-semibold text-text-primary mb-3">Application Pipeline Statuses</h3>
          <div className="space-y-2.5 text-xs">
            {stats?.status_distribution && Object.keys(stats.status_distribution).length > 0 ? (
              Object.entries(stats.status_distribution).map(([statusKey, count]) => (
                <div key={statusKey} className="flex items-center justify-between py-1 border-b border-border/50">
                  <span className="text-text-secondary font-medium">{statusKey}</span>
                  <span className="px-2 py-0.5 rounded-md bg-surfaceHover font-semibold text-text-primary">
                    {count}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-xs text-text-muted py-4 text-center">No applications queued yet</p>
            )}
          </div>
        </div>

        {/* Sources Breakdown */}
        <div className="fluent-card p-5">
          <h3 className="text-sm font-semibold text-text-primary mb-3">Job Source Providers</h3>
          <div className="space-y-2.5 text-xs">
            {stats?.source_distribution && Object.keys(stats.source_distribution).length > 0 ? (
              Object.entries(stats.source_distribution).map(([src, count]) => (
                <div key={src} className="flex items-center justify-between py-1 border-b border-border/50">
                  <span className="text-text-secondary font-medium capitalize">{src}</span>
                  <span className="px-2 py-0.5 rounded-md bg-surfaceHover font-semibold text-text-primary">
                    {count} listings
                  </span>
                </div>
              ))
            ) : (
              <p className="text-xs text-text-muted py-4 text-center">No source listings discovered yet</p>
            )}
          </div>
        </div>
      </div>

      {/* Recent Discovered Jobs */}
      <div className="fluent-card p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-text-primary">Recent Job Listings</h3>
          <Link to="/jobs" className="text-xs text-primary hover:underline flex items-center gap-1">
            <span>View all jobs</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-text-muted border-b border-border">
              <tr>
                <th className="pb-2 font-medium">Job Title</th>
                <th className="pb-2 font-medium">Company</th>
                <th className="pb-2 font-medium">Location</th>
                <th className="pb-2 font-medium">Match</th>
                <th className="pb-2 font-medium">Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              {stats?.recent_jobs && stats.recent_jobs.length > 0 ? (
                stats.recent_jobs.map((j) => (
                  <tr key={j.id} className="hover:bg-surfaceHover/40 transition-colors">
                    <td className="py-2.5 font-medium text-text-primary">{j.title}</td>
                    <td className="py-2.5 text-text-secondary">{j.company}</td>
                    <td className="py-2.5 text-text-muted">{j.location}</td>
                    <td className="py-2.5">
                      <span
                        className={`font-semibold ${
                          j.match_score >= 75 ? "text-success" : j.match_score >= 50 ? "text-warning" : "text-danger"
                        }`}
                      >
                        {j.match_score}%
                      </span>
                    </td>
                    <td className="py-2.5 text-text-muted capitalize">{j.source_platform}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-4 text-center text-text-muted">
                    No recent listings found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
