import React, { useState, useEffect } from "react";
import {
  Shield,
  HardDrive,
  Globe,
  Lock,
  Save,
  CheckCircle2,
  FileCheck,
  AlertTriangle,
  Info,
} from "lucide-react";
import { useAutomationSettings, useAppMutations } from "../api/hooks";

export const SettingsPage: React.FC = () => {
  const { data: settings } = useAutomationSettings();
  const { updateAutomationSettings } = useAppMutations();

  const [retentionDays, setRetentionDays] = useState(30);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (settings?.log_retention_days) {
      setRetentionDays(settings.log_retention_days);
    }
  }, [settings]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    await updateAutomationSettings.mutateAsync({ log_retention_days: retentionDays });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary tracking-tight">System & Security Settings</h1>
        <p className="text-xs md:text-sm text-text-muted mt-0.5">
          Localhost isolation, local file storage paths, platform restrictions, and log retention.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Localhost & Isolation Security */}
        <div className="fluent-card p-6 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-border">
            <Lock className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold text-text-primary">Localhost Security & Isolation</h3>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-start gap-2.5 p-3 rounded-lg bg-surfaceHover/50 border border-border">
              <CheckCircle2 className="w-4 h-4 text-success shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-text-primary block">Loopback Only (127.0.0.1)</span>
                <p className="text-text-muted mt-0.5">
                  Both FastAPI and Vite bind exclusively to loopback addresses. The application is completely inaccessible from the public internet or local area network.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-2.5 p-3 rounded-lg bg-surfaceHover/50 border border-border">
              <CheckCircle2 className="w-4 h-4 text-success shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-text-primary block">Strict CORS Protection</span>
                <p className="text-text-muted mt-0.5">
                  API endpoints strictly check origin headers to prevent malicious websites from triggering unauthorized background requests.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-2.5 p-3 rounded-lg bg-surfaceHover/50 border border-border">
              <CheckCircle2 className="w-4 h-4 text-success shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-text-primary block">Local-First Data Privacy</span>
                <p className="text-text-muted mt-0.5">
                  Candidate resumes, profiles, and history never leave your computer. All text parsing and matching runs locally.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Local File Storage Paths */}
        <div className="fluent-card p-6 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-border">
            <HardDrive className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold text-text-primary">Persistence & Local Storage</h3>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="p-2.5 rounded bg-surfaceHover/40 border border-border">
              <span className="text-text-muted block text-[10px] font-semibold uppercase">SQLite Database</span>
              <code className="text-primary font-mono text-[11px]">data/applypilot.db</code>
            </div>

            <div className="p-2.5 rounded bg-surfaceHover/40 border border-border">
              <span className="text-text-muted block text-[10px] font-semibold uppercase">Resumes Directory</span>
              <code className="text-primary font-mono text-[11px]">resumes/</code>
            </div>

            <div className="p-2.5 rounded bg-surfaceHover/40 border border-border">
              <span className="text-text-muted block text-[10px] font-semibold uppercase">Browser Profile Directory</span>
              <code className="text-primary font-mono text-[11px]">data/browser_profile/</code>
            </div>

            <div className="p-2.5 rounded bg-surfaceHover/40 border border-border">
              <span className="text-text-muted block text-[10px] font-semibold uppercase">Diagnostic Screenshots</span>
              <code className="text-primary font-mono text-[11px]">data/screenshots/</code>
            </div>

            <div className="p-2.5 rounded bg-surfaceHover/40 border border-border">
              <span className="text-text-muted block text-[10px] font-semibold uppercase">Audit Log Files</span>
              <code className="text-primary font-mono text-[11px]">logs/applypilot.log</code>
            </div>
          </div>
        </div>

        {/* Platform Compliance & Limitations */}
        <div className="fluent-card p-6 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-border">
            <AlertTriangle className="w-4 h-4 text-warning" />
            <h3 className="text-sm font-semibold text-text-primary">Platform Restrictions & Compliance</h3>
          </div>

          <p className="text-xs text-text-muted leading-relaxed">
            ApplyPilot is designed with ethical automation boundaries. We do not evade platform restrictions, bypass anti-bot shields, or solve CAPTCHAs.
          </p>

          <div className="space-y-2 text-xs text-text-secondary">
            <div className="p-2.5 rounded bg-surfaceHover/30 border border-border flex items-start gap-2">
              <Info className="w-4 h-4 text-primary shrink-0 mt-0.5" />
              <span>
                <strong>LinkedIn & Wellfound:</strong> Automated submission is restricted by platform terms. ApplyPilot transparently switches these jobs to the Manual Assistance Queue.
              </span>
            </div>

            <div className="p-2.5 rounded bg-surfaceHover/30 border border-border flex items-start gap-2">
              <Info className="w-4 h-4 text-primary shrink-0 mt-0.5" />
              <span>
                <strong>CAPTCHA & MFA:</strong> If a security checkpoint is encountered, ApplyPilot immediately pauses and preserves the visible browser for your intervention.
              </span>
            </div>
          </div>
        </div>

        {/* Log Retention & Maintenance */}
        <div className="fluent-card p-6 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-border">
            <FileCheck className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold text-text-primary">Log Retention Setting</h3>
          </div>

          <form onSubmit={handleSave} className="space-y-4 text-xs">
            <div>
              <label className="text-xs font-medium text-text-secondary">
                Audit Log Retention Window (Days)
              </label>
              <input
                type="number"
                min="1"
                max="365"
                value={retentionDays}
                onChange={(e) => setRetentionDays(Number(e.target.value))}
                className="fluent-input w-full mt-1.5"
              />
              <span className="text-[11px] text-text-muted block mt-1">
                Logs older than this threshold will be pruned on demand.
              </span>
            </div>

            <button
              type="submit"
              disabled={updateAutomationSettings.isPending}
              className="fluent-button fluent-button-primary text-xs"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{updateAutomationSettings.isPending ? "Saving..." : saved ? "Saved!" : "Update Retention"}</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
