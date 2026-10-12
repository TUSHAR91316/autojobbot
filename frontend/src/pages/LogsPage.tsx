import React, { useState } from "react";
import {
  FileText,
  Search,
  Trash2,
  Filter,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Activity,
  Info,
} from "lucide-react";
import { useActivityLogs, useAppMutations } from "../api/hooks";

export const LogsPage: React.FC = () => {
  const [levelFilter, setLevelFilter] = useState("all");
  const [search, setSearch] = useState("");

  const { data: logs = [], isLoading } = useActivityLogs({
    level: levelFilter !== "all" ? levelFilter : undefined,
    search: search || undefined,
  });

  const { clearLogs } = useAppMutations();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Activity Logs & Audit Trail</h1>
          <p className="text-xs md:text-sm text-text-muted mt-0.5">
            Transparent event logs of session transitions, discovery feeds, and automation steps.
          </p>
        </div>

        <button
          onClick={() => clearLogs.mutate()}
          disabled={clearLogs.isPending || logs.length === 0}
          className="fluent-button fluent-button-secondary text-xs text-danger self-start sm:self-auto hover:border-danger/30"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Clear Logs</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="fluent-card p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted" />
          <input
            type="text"
            placeholder="Search log messages..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="fluent-input w-full pl-8 text-xs"
          />
        </div>

        <div className="flex items-center gap-1.5 flex-wrap text-xs">
          <span className="text-text-muted mr-1">Level:</span>
          {["all", "INFO", "ACTION", "SUCCESS", "WARNING", "ERROR"].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setLevelFilter(lvl)}
              className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${
                levelFilter === lvl
                  ? "bg-primary text-slate-900 font-semibold"
                  : "bg-surfaceHover text-text-secondary hover:text-text-primary"
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Logs Table */}
      <div className="fluent-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-surfaceHover/50 text-text-muted border-b border-border">
              <tr>
                <th className="py-3 px-4 font-semibold">Timestamp</th>
                <th className="py-3 px-4 font-semibold">Level</th>
                <th className="py-3 px-4 font-semibold">Action</th>
                <th className="py-3 px-4 font-semibold">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              {isLoading ? (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-text-muted">
                    Loading activity logs...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-12 text-center text-text-muted">
                    <FileText className="w-8 h-8 mx-auto mb-2 opacity-40" />
                    No activity logs recorded yet.
                  </td>
                </tr>
              ) : (
                logs.map((log) => {
                  const dateFormatted = new Date(log.created_at).toLocaleTimeString(undefined, {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  });

                  return (
                    <tr key={log.id} className="hover:bg-surfaceHover/30 transition-colors font-mono">
                      <td className="py-2.5 px-4 text-text-muted text-[11px] whitespace-nowrap">
                        {dateFormatted}
                      </td>
                      <td className="py-2.5 px-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            log.level === "ERROR"
                              ? "bg-danger/15 text-danger"
                              : log.level === "WARNING"
                              ? "bg-warning/15 text-warning"
                              : log.level === "SUCCESS"
                              ? "bg-success/15 text-success"
                              : log.level === "ACTION"
                              ? "bg-primary/15 text-primary"
                              : "bg-surfaceHover text-text-muted"
                          }`}
                        >
                          {log.level}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 font-semibold text-text-secondary whitespace-nowrap">
                        {log.action}
                      </td>
                      <td className="py-2.5 px-4 text-text-primary font-sans text-xs">
                        {log.message}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
