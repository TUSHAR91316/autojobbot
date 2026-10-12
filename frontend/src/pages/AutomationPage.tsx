import React, { useState, useEffect } from "react";
import {
  Play,
  Pause,
  Square,
  RotateCcw,
  Sparkles,
  Download,
  ShieldCheck,
  AlertTriangle,
  Clock,
  Save,
  CheckCircle2,
  Sliders,
  Settings as SettingsIcon,
} from "lucide-react";
import {
  useAutomationSettings,
  useAutomationStatus,
  useAppMutations,
} from "../api/hooks";
import { AutomationSettings } from "../types";
import { API_BASE_URL } from "../api/client";

export const AutomationPage: React.FC = () => {
  const { data: settings, isLoading } = useAutomationSettings();
  const { data: status } = useAutomationStatus();

  const {
    updateAutomationSettings,
    startAutomation,
    pauseAutomation,
    resumeAutomation,
    stopAutomation,
    retryFailed,
    autoBuildQueue,
    discoverJobs,
  } = useAppMutations();

  const [formData, setFormData] = useState<Partial<AutomationSettings>>({});
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  if (isLoading) {
    return <div className="p-8 text-center text-text-muted animate-pulse">Loading settings...</div>;
  }

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await updateAutomationSettings.mutateAsync(formData);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error(err);
    }
  };

  const isRunning = status?.is_active && !status?.is_paused;
  const isPaused = status?.is_paused;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Automation Controls & Settings</h1>
          <p className="text-xs md:text-sm text-text-muted mt-0.5">
            Configure session limits, safe simulation modes, rate-limiting delays, and execution safety guards.
          </p>
        </div>

        <button
          onClick={handleSaveSettings}
          disabled={updateAutomationSettings.isPending}
          className="fluent-button fluent-button-primary text-xs self-start sm:self-auto"
        >
          <Save className="w-3.5 h-3.5" />
          <span>{updateAutomationSettings.isPending ? "Saving..." : saved ? "Settings Saved!" : "Save Settings"}</span>
        </button>
      </div>

      {/* Main Interactive Control Bar */}
      <div className="fluent-card p-5 border-primary/30 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-primary" />
            <span className="font-semibold text-text-primary text-sm">Session Control Panel</span>
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                isRunning
                  ? "bg-success/20 text-success"
                  : isPaused
                  ? "bg-warning/20 text-warning"
                  : "bg-surfaceHover text-text-muted"
              }`}
            >
              Status: {status?.status || "IDLE"}
            </span>
          </div>

          <span className="text-xs text-text-muted">
            Bounded Concurrency: <strong className="text-text-primary">1 (Strict single-thread worker)</strong>
          </span>
        </div>

        {/* Live Session Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          {!status?.is_active ? (
            <button
              onClick={() =>
                startAutomation.mutate({
                  target: formData.target_applications_per_session || 15,
                  delay: formData.delay_between_attempts_sec || 2.0,
                })
              }
              disabled={startAutomation.isPending}
              className="fluent-button fluent-button-primary text-xs py-2 px-4"
            >
              <Play className="w-4 h-4" />
              <span>Start Session</span>
            </button>
          ) : (
            <>
              {isRunning && (
                <button
                  onClick={() => pauseAutomation.mutate()}
                  className="fluent-button fluent-button-secondary text-xs py-2 px-4 text-warning"
                >
                  <Pause className="w-4 h-4" />
                  <span>Pause Session</span>
                </button>
              )}
              {isPaused && (
                <button
                  onClick={() => resumeAutomation.mutate()}
                  className="fluent-button fluent-button-secondary text-xs py-2 px-4 text-success"
                >
                  <Play className="w-4 h-4" />
                  <span>Resume Session</span>
                </button>
              )}
              <button
                onClick={() => stopAutomation.mutate()}
                className="fluent-button fluent-button-secondary text-xs py-2 px-4 text-danger"
              >
                <Square className="w-4 h-4" />
                <span>Stop Immediately</span>
              </button>
            </>
          )}

          <button
            onClick={() => autoBuildQueue.mutate(formData.target_applications_per_session || 15)}
            disabled={autoBuildQueue.isPending}
            className="fluent-button fluent-button-secondary text-xs py-2 px-3"
          >
            <Sparkles className="w-3.5 h-3.5 text-primary" />
            <span>Build Queue</span>
          </button>

          <button
            onClick={() => discoverJobs.mutate("all")}
            disabled={discoverJobs.isPending}
            className="fluent-button fluent-button-secondary text-xs py-2 px-3"
          >
            <Sparkles className="w-3.5 h-3.5 text-primary" />
            <span>Discover Jobs</span>
          </button>

          <button
            onClick={() => retryFailed.mutate()}
            disabled={retryFailed.isPending}
            className="fluent-button fluent-button-secondary text-xs py-2 px-3"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Retry Eligible Failures</span>
          </button>

          <a
            href={`${API_BASE_URL}/history/export/csv`}
            download="applypilot_results.csv"
            className="fluent-button fluent-button-secondary text-xs py-2 px-3"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Results</span>
          </a>
        </div>

        {/* Status ticker */}
        <div className="text-xs text-text-muted flex items-center gap-2 pt-2">
          <Clock className="w-3.5 h-3.5" />
          <span>
            {status?.current_action || "Ready to execute session."}
          </span>
        </div>
      </div>

      {/* Configuration Form */}
      <form onSubmit={handleSaveSettings} className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left Column: Sliders & Limits */}
        <div className="fluent-card p-6 space-y-5">
          <h3 className="text-sm font-semibold text-text-primary uppercase tracking-wider pb-2 border-b border-border">
            Session Targets & Rate Limits
          </h3>

          {/* Target applications (1-15) */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="font-medium text-text-secondary">Target Applications per Session</span>
              <span className="font-bold text-primary">
                {formData.target_applications_per_session || 15} / 15 max
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="15"
              step="1"
              value={formData.target_applications_per_session || 15}
              onChange={(e) =>
                setFormData({ ...formData, target_applications_per_session: Number(e.target.value) })
              }
              className="w-full accent-primary"
            />
            <p className="text-[11px] text-text-muted">
              Safety limit: Maximum 15 applications per session to avoid spamming or account flagging.
            </p>
          </div>

          {/* Delay between attempts (1-5 seconds) */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="font-medium text-text-secondary">Delay Between Workflow Attempts</span>
              <span className="font-bold text-primary">
                {formData.delay_between_attempts_sec || 2.0} seconds
              </span>
            </div>
            <input
              type="range"
              min="1.0"
              max="5.0"
              step="0.5"
              value={formData.delay_between_attempts_sec || 2.0}
              onChange={(e) =>
                setFormData({ ...formData, delay_between_attempts_sec: Number(e.target.value) })
              }
              className="w-full accent-primary"
            />
            <p className="text-[11px] text-text-muted">
              User-selectable preference (1.0 to 5.0s). Strict platform rate limits take precedence.
            </p>
          </div>

          {/* Minimum match score */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="font-medium text-text-secondary">Minimum Job Match Score</span>
              <span className="font-bold text-primary">{formData.min_match_score || 60}%</span>
            </div>
            <input
              type="range"
              min="30"
              max="90"
              step="5"
              value={formData.min_match_score || 60}
              onChange={(e) =>
                setFormData({ ...formData, min_match_score: Number(e.target.value) })
              }
              className="w-full accent-primary"
            />
          </div>

          {/* Stop after failures */}
          <div>
            <label className="text-xs font-medium text-text-secondary">Stop After Consecutive Failures</label>
            <input
              type="number"
              min="1"
              max="10"
              value={formData.stop_after_failures || 3}
              onChange={(e) =>
                setFormData({ ...formData, stop_after_failures: Number(e.target.value) })
              }
              className="fluent-input w-full mt-1 text-xs"
            />
          </div>
        </div>

        {/* Right Column: Execution Rules & Safety Toggles */}
        <div className="fluent-card p-6 space-y-4">
          <h3 className="text-sm font-semibold text-text-primary uppercase tracking-wider pb-2 border-b border-border">
            Safety & Workflow Execution Modes
          </h3>

          {/* Safe Simulation Mode Toggle */}
          <label className="flex items-start gap-3 p-3 rounded-lg bg-surfaceHover/40 border border-border cursor-pointer">
            <input
              type="checkbox"
              checked={formData.simulation_mode ?? true}
              onChange={(e) => setFormData({ ...formData, simulation_mode: e.target.checked })}
              className="mt-0.5 accent-primary rounded"
            />
            <div className="text-xs">
              <span className="font-semibold text-text-primary block">Safe Simulation Mode (Recommended)</span>
              <p className="text-text-muted mt-0.5 leading-relaxed">
                Exercises the complete pipeline with local synthetic test pages without submitting to external job websites.
              </p>
            </div>
          </label>

          {/* Duplicate skipping toggle */}
          <label className="flex items-start gap-3 p-3 rounded-lg bg-surfaceHover/40 border border-border cursor-pointer">
            <input
              type="checkbox"
              checked={formData.skip_duplicates ?? true}
              onChange={(e) => setFormData({ ...formData, skip_duplicates: e.target.checked })}
              className="mt-0.5 accent-primary rounded"
            />
            <div className="text-xs">
              <span className="font-semibold text-text-primary block">Skip Duplicate Applications</span>
              <p className="text-text-muted mt-0.5 leading-relaxed">
                Prevents re-applying to identical URLs, job IDs, or company/title combinations.
              </p>
            </div>
          </label>

          {/* Human review before submit toggle */}
          <label className="flex items-start gap-3 p-3 rounded-lg bg-surfaceHover/40 border border-border cursor-pointer">
            <input
              type="checkbox"
              checked={formData.require_review_before_submit ?? false}
              onChange={(e) =>
                setFormData({ ...formData, require_review_before_submit: e.target.checked })
              }
              className="mt-0.5 accent-primary rounded"
            />
            <div className="text-xs">
              <span className="font-semibold text-text-primary block">Require Review Before Submission</span>
              <p className="text-text-muted mt-0.5 leading-relaxed">
                Pauses and places applications in "Awaiting Review" for manual sign-off before submission.
              </p>
            </div>
          </label>

          {/* External to manual action toggle */}
          <label className="flex items-start gap-3 p-3 rounded-lg bg-surfaceHover/40 border border-border cursor-pointer">
            <input
              type="checkbox"
              checked={formData.include_external_in_manual_queue ?? true}
              onChange={(e) =>
                setFormData({ ...formData, include_external_in_manual_queue: e.target.checked })
              }
              className="mt-0.5 accent-primary rounded"
            />
            <div className="text-xs">
              <span className="font-semibold text-text-primary block">Route External Sites to Manual Queue</span>
              <p className="text-text-muted mt-0.5 leading-relaxed">
                Respects platform restrictions by placing LinkedIn and external applications into the manual assistance queue.
              </p>
            </div>
          </label>

          {/* Stop on CAPTCHA */}
          <label className="flex items-start gap-3 p-3 rounded-lg bg-surfaceHover/40 border border-border cursor-pointer">
            <input
              type="checkbox"
              checked={formData.stop_on_captcha_mfa ?? true}
              onChange={(e) => setFormData({ ...formData, stop_on_captcha_mfa: e.target.checked })}
              className="mt-0.5 accent-primary rounded"
            />
            <div className="text-xs">
              <span className="font-semibold text-text-primary block">Stop on CAPTCHA or MFA Challenge</span>
              <p className="text-text-muted mt-0.5 leading-relaxed">
                Never bypasses access controls. Pauses the session and preserves browser state for you.
              </p>
            </div>
          </label>
        </div>
      </form>
    </div>
  );
};
