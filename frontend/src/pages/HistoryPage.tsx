import React, { useState } from "react";
import {
  History,
  Search,
  Download,
  ExternalLink,
  CheckCircle,
  XCircle,
  Clock,
  FileText,
  AlertCircle,
} from "lucide-react";
import { useHistory } from "../api/hooks";
import { API_BASE_URL } from "../api/client";
import { JobApplication } from "../types";
import { ReviewModal } from "../components/queue/ReviewModal";

export const HistoryPage: React.FC = () => {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [detailApp, setDetailApp] = useState<JobApplication | null>(null);

  const { data: history = [], isLoading } = useHistory({
    status: statusFilter !== "all" ? statusFilter : undefined,
    search: search || undefined,
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Application History</h1>
          <p className="text-xs md:text-sm text-text-muted mt-0.5">
            Audit trail of completed, manual, and skipped applications persisted in SQLite.
          </p>
        </div>

        <a
          href={`${API_BASE_URL}/history/export/csv`}
          download="applypilot_history.csv"
          className="fluent-button fluent-button-secondary text-xs self-start sm:self-auto"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export History CSV</span>
        </a>
      </div>

      {/* Filter Bar */}
      <div className="fluent-card p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted" />
          <input
            type="text"
            placeholder="Search by job title or company..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="fluent-input w-full pl-8 text-xs"
          />
        </div>

        <div className="flex items-center gap-1.5 flex-wrap text-xs">
          <span className="text-text-muted mr-1">Status:</span>
          {["all", "SUBMITTED", "MANUAL_ACTION_REQUIRED", "FAILED", "SKIPPED"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${
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

      {/* History Table */}
      <div className="fluent-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-surfaceHover/50 text-text-muted border-b border-border">
              <tr>
                <th className="py-3 px-4 font-semibold">Date</th>
                <th className="py-3 px-4 font-semibold">Company</th>
                <th className="py-3 px-4 font-semibold">Job Title</th>
                <th className="py-3 px-4 font-semibold">Source</th>
                <th className="py-3 px-4 font-semibold">Match</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold">Last Action</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              {isLoading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-text-muted">
                    Loading history records...
                  </td>
                </tr>
              ) : history.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-text-muted">
                    <History className="w-8 h-8 mx-auto mb-2 opacity-40" />
                    No application history found matching current criteria.
                  </td>
                </tr>
              ) : (
                history.map((app) => {
                  const job = app.job;
                  const dateStr = app.applied_at || app.updated_at;
                  const formattedDate = dateStr
                    ? new Date(dateStr).toLocaleDateString(undefined, {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : "—";

                  return (
                    <tr key={app.id} className="hover:bg-surfaceHover/30 transition-colors">
                      <td className="py-3 px-4 text-text-muted font-mono text-[11px] whitespace-nowrap">
                        {formattedDate}
                      </td>
                      <td className="py-3 px-4 font-medium text-text-primary whitespace-nowrap">
                        {job?.company}
                      </td>
                      <td className="py-3 px-4 text-text-primary font-medium">{job?.title}</td>
                      <td className="py-3 px-4 text-text-muted capitalize whitespace-nowrap">
                        {job?.source_platform}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span
                          className={`font-semibold ${
                            (job?.match_score || 0) >= 75
                              ? "text-success"
                              : (job?.match_score || 0) >= 50
                              ? "text-warning"
                              : "text-danger"
                          }`}
                        >
                          {job?.match_score}%
                        </span>
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            app.status === "SUBMITTED"
                              ? "bg-success/15 text-success"
                              : app.status === "FAILED"
                              ? "bg-danger/15 text-danger"
                              : app.status === "MANUAL_ACTION_REQUIRED"
                              ? "bg-primary/15 text-primary"
                              : "bg-surfaceHover text-text-muted"
                          }`}
                        >
                          {app.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-text-muted max-w-xs truncate" title={app.last_action}>
                        {app.last_action}
                      </td>
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => setDetailApp(app)}
                            className="p-1 text-text-muted hover:text-text-primary rounded hover:bg-surfaceHover"
                            title="Inspect application details"
                          >
                            <FileText className="w-3.5 h-3.5" />
                          </button>

                          {job?.original_url && (
                            <a
                              href={job.original_url}
                              target="_blank"
                              rel="noreferrer"
                              className="p-1 text-text-muted hover:text-text-primary rounded hover:bg-surfaceHover"
                              title="Open original job posting"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Review / Detail Modal */}
      <ReviewModal app={detailApp} onClose={() => setDetailApp(null)} />
    </div>
  );
};
