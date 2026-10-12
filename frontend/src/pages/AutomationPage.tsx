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
  Globe,
  Monitor,
  XCircle,
  Loader2,
  Check,
  KeyRound,
  ExternalLink,
  MapPin,
  Lock,
  Unlock,
  Terminal,
} from "lucide-react";
import {
  useAutomationSettings,
  useAutomationStatus,
  useBrowserSessions,
  useProfile,
  useAppMutations,
} from "../api/hooks";
import { AutomationSettings } from "../types";
import { API_BASE_URL } from "../api/client";
import { Link } from "react-router-dom";

export const AutomationPage: React.FC = () => {
  const { data: settings, isLoading } = useAutomationSettings();
  const { data: status } = useAutomationStatus();
  const { data: sessions, refetch: refetchSessions } = useBrowserSessions();
  const { data: profile } = useProfile();

  const {
    updateAutomationSettings,
    startAutomation,
    pauseAutomation,
    resumeAutomation,
    stopAutomation,
    retryFailed,
    autoBuildQueue,
    discoverJobs,
    launchDesktopBrowser,
    closeDesktopBrowser,
    toggleSimulationMode,
    applyCustomUrlInBrowser,
    openPortalLogin,
    connectChromeCdp,
  } = useAppMutations();

  const [formData, setFormData] = useState<Partial<AutomationSettings>>({});
  const [saved, setSaved] = useState(false);
  const [quickUrl, setQuickUrl] = useState("");
  const [quickApplyMsg, setQuickApplyMsg] = useState("");
  const [cdpPortInput, setCdpPortInput] = useState("http://127.0.0.1:9222");
  const [cdpMsg, setCdpMsg] = useState("");

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

  const handleQuickUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickUrl.trim()) return;
    try {
      setQuickApplyMsg("Launching browser to apply...");
      const res = await applyCustomUrlInBrowser.mutateAsync({
        url: quickUrl.trim(),
        title: "Direct Job Application",
        company: "Direct Employer",
      });
      setQuickApplyMsg(res.message || "Browser application completed!");
      setQuickUrl("");
      setTimeout(() => setQuickApplyMsg(""), 5000);
    } catch (err: any) {
      setQuickApplyMsg(err.response?.data?.detail || err.message || "Failed to run browser automation");
      setTimeout(() => setQuickApplyMsg(""), 5000);
    }
  };

  const handleCdpConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCdpMsg("Connecting to your Chrome instance...");
      const res = await connectChromeCdp.mutateAsync(cdpPortInput.trim());
      setCdpMsg(res.message || "Connected to running Chrome!");
      setTimeout(() => setCdpMsg(""), 6000);
    } catch (err: any) {
      setCdpMsg(err.response?.data?.detail || "Could not connect to Chrome. Ensure Chrome is running with --remote-debugging-port=9222");
      setTimeout(() => setCdpMsg(""), 6000);
    }
  };

  const isRunning = status?.is_active && !status?.is_paused;
  const isPaused = status?.is_paused;
  const isSim = status?.simulation_mode ?? settings?.simulation_mode ?? false;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Browser Automation & Settings</h1>
          <p className="text-xs md:text-sm text-text-muted mt-0.5">
            Configure the <strong>Live Desktop Browser Bot</strong>, saved login sessions (LinkedIn, Indeed, Naukri), real-time India location preference, and execution limits.
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

      {/* CANDIDATE LOCATION & INDIA PREFERENCE REALTIME BANNER */}
      <div className="fluent-card p-4 bg-gradient-to-r from-success/10 via-surface to-surface border-success/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-success/20 text-success flex items-center justify-center shrink-0">
            <MapPin className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-text-primary">Real-Time Candidate Location:</span>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-success/20 text-success">
                {profile?.current_location || "Bengaluru, India"}
              </span>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-primary/15 text-primary">
                India Preferred 🇮🇳
              </span>
            </div>
            <p className="text-[11px] text-text-muted mt-0.5">
              Target Hubs: <strong>Bengaluru, Hyderabad, Pune, Mumbai, Delhi-NCR, Remote India</strong>. Match score boosts eligible India jobs to 100%.
            </p>
          </div>
        </div>

        <Link
          to="/profile"
          className="fluent-button fluent-button-secondary text-xs py-1.5 px-3 shrink-0 self-start sm:self-auto"
        >
          <span>Edit Location in Profile</span>
        </Link>
      </div>

      {/* BROWSER LOGIN CREDENTIALS & SESSIONS CARD */}
      <div className="fluent-card p-5 border-primary/30 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <KeyRound className="w-5 h-5 text-primary" />
            <h3 className="text-sm font-bold text-text-primary">
              Browser Login Credentials & Session Cache
            </h3>
          </div>
          <span className="text-xs text-text-muted">
            Saved Cookies: <strong className="text-text-primary">{sessions?.total_cookies || 0} active</strong>
          </span>
        </div>

        <p className="text-xs text-text-muted leading-relaxed">
          Log in once using the buttons below. Your login credentials, session cookies, and authentication tokens are saved permanently in ApplyPilot's persistent browser profile (<code>data/browser_profile</code>). The automation bot will use your active accounts to apply seamlessly without login walls or repetitive sign-ins!
        </p>

        {/* Portal Login Badges & Quick Sign-In Buttons */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-1">
          {/* LinkedIn */}
          <div className="p-3 rounded-lg bg-surfaceHover/50 border border-border flex flex-col justify-between space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-text-primary flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-blue-500" /> LinkedIn
              </span>
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                  sessions?.linkedin ? "bg-success/20 text-success" : "bg-surfaceHover text-text-muted"
                }`}
              >
                {sessions?.linkedin ? "Active Session" : "Not Logged In"}
              </span>
            </div>
            <button
              onClick={() => openPortalLogin.mutate("linkedin")}
              disabled={openPortalLogin.isPending}
              className="fluent-button fluent-button-secondary text-[11px] w-full py-1.5 justify-center font-medium"
            >
              <ExternalLink className="w-3 h-3" />
              <span>{sessions?.linkedin ? "Open LinkedIn Tab" : "Sign In to LinkedIn"}</span>
            </button>
          </div>

          {/* Indeed */}
          <div className="p-3 rounded-lg bg-surfaceHover/50 border border-border flex flex-col justify-between space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-text-primary flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-indigo-500" /> Indeed
              </span>
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                  sessions?.indeed ? "bg-success/20 text-success" : "bg-surfaceHover text-text-muted"
                }`}
              >
                {sessions?.indeed ? "Active Session" : "Not Logged In"}
              </span>
            </div>
            <button
              onClick={() => openPortalLogin.mutate("indeed")}
              disabled={openPortalLogin.isPending}
              className="fluent-button fluent-button-secondary text-[11px] w-full py-1.5 justify-center font-medium"
            >
              <ExternalLink className="w-3 h-3" />
              <span>{sessions?.indeed ? "Open Indeed Tab" : "Sign In to Indeed"}</span>
            </button>
          </div>

          {/* Naukri.com (India) */}
          <div className="p-3 rounded-lg bg-surfaceHover/50 border border-border flex flex-col justify-between space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-text-primary flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500" /> Naukri (India 🇮🇳)
              </span>
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                  sessions?.naukri ? "bg-success/20 text-success" : "bg-surfaceHover text-text-muted"
                }`}
              >
                {sessions?.naukri ? "Active Session" : "Not Logged In"}
              </span>
            </div>
            <button
              onClick={() => openPortalLogin.mutate("naukri")}
              disabled={openPortalLogin.isPending}
              className="fluent-button fluent-button-secondary text-[11px] w-full py-1.5 justify-center font-medium"
            >
              <ExternalLink className="w-3 h-3" />
              <span>{sessions?.naukri ? "Open Naukri Tab" : "Sign In to Naukri"}</span>
            </button>
          </div>

          {/* Wellfound / AngelList */}
          <div className="p-3 rounded-lg bg-surfaceHover/50 border border-border flex flex-col justify-between space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-text-primary flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-rose-500" /> Wellfound
              </span>
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                  sessions?.wellfound ? "bg-success/20 text-success" : "bg-surfaceHover text-text-muted"
                }`}
              >
                {sessions?.wellfound ? "Active Session" : "Not Logged In"}
              </span>
            </div>
            <button
              onClick={() => openPortalLogin.mutate("wellfound")}
              disabled={openPortalLogin.isPending}
              className="fluent-button fluent-button-secondary text-[11px] w-full py-1.5 justify-center font-medium"
            >
              <ExternalLink className="w-3 h-3" />
              <span>{sessions?.wellfound ? "Open Wellfound Tab" : "Sign In to Wellfound"}</span>
            </button>
          </div>
        </div>

        {/* Alternative: Connect to Running Chrome over CDP */}
        <div className="pt-2 border-t border-border">
          <details className="text-xs text-text-secondary cursor-pointer">
            <summary className="font-semibold text-text-primary hover:text-primary transition-colors flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5" />
              <span>Alternative: Connect directly to your existing open Chrome browser (CDP Port 9222)</span>
            </summary>
            <div className="mt-3 p-3 bg-surfaceHover/40 rounded-lg space-y-2 text-xs">
              <p className="text-text-muted leading-relaxed">
                If you already have Google Chrome open with all your extensions, passwords, and accounts signed in, you can start Chrome with remote debugging:
              </p>
              <pre className="p-2 rounded bg-slate-950 font-mono text-[11px] text-primary overflow-x-auto select-all">
                chrome.exe --remote-debugging-port=9222
              </pre>
              <form onSubmit={handleCdpConnect} className="flex gap-2 pt-1">
                <input
                  type="text"
                  value={cdpPortInput}
                  onChange={(e) => setCdpPortInput(e.target.value)}
                  placeholder="http://127.0.0.1:9222"
                  className="fluent-input text-xs flex-1"
                />
                <button
                  type="submit"
                  disabled={connectChromeCdp.isPending}
                  className="fluent-button fluent-button-secondary text-xs px-3"
                >
                  {connectChromeCdp.isPending ? "Connecting..." : "Connect to Chrome"}
                </button>
              </form>
              {cdpMsg && (
                <p className="text-[11px] text-primary font-medium mt-1">{cdpMsg}</p>
              )}
            </div>
          </details>
        </div>
      </div>

      {/* PRIMARY BROWSER BOT MODE & QUICK ACTION */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Mode Card */}
        <div className="fluent-card p-5 border-primary/40 md:col-span-2 flex flex-col justify-between space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary/15 flex items-center justify-center text-primary shrink-0">
                <Monitor className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-text-primary">
                    {isSim ? "Dry Run Simulation Mode" : "Live Desktop Browser Bot (Active)"}
                  </h3>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      isSim ? "bg-warning/20 text-warning" : "bg-success/20 text-success"
                    }`}
                  >
                    {isSim ? "SIMULATION" : "LIVE BROWSER"}
                  </span>
                </div>
                <p className="text-xs text-text-muted mt-1 leading-relaxed">
                  {isSim
                    ? "Dry run mode: Tests scheduling, queue flow, and cover letter generation without launching a visible browser."
                    : "Real automation: Launches a visible Chromium browser window right on your screen, navigates to application URLs, auto-types your profile info, uploads your active resume, and applies for you!"}
                </p>
              </div>
            </div>

            <button
              onClick={() => toggleSimulationMode.mutate()}
              disabled={toggleSimulationMode.isPending}
              className={`fluent-button text-xs py-1.5 px-3 shrink-0 font-semibold ${
                isSim ? "fluent-button-primary" : "fluent-button-secondary text-warning"
              }`}
            >
              {isSim ? "Switch to Live Browser" : "Switch to Simulation"}
            </button>
          </div>

          {/* Quick Apply direct to URL */}
          <form onSubmit={handleQuickUrlSubmit} className="pt-2 border-t border-border flex flex-col sm:flex-row gap-2">
            <input
              type="url"
              placeholder="Paste any job URL to test browser automation (e.g. LinkedIn, Greenhouse, Lever)..."
              value={quickUrl}
              onChange={(e) => setQuickUrl(e.target.value)}
              className="fluent-input text-xs flex-1"
            />
            <button
              type="submit"
              disabled={applyCustomUrlInBrowser.isPending || !quickUrl.trim()}
              className="fluent-button fluent-button-primary text-xs py-1.5 px-3 shrink-0"
            >
              {applyCustomUrlInBrowser.isPending ? "Applying..." : "Apply in Browser"}
            </button>
          </form>

          {quickApplyMsg && (
            <div className="p-2 rounded bg-primary/10 border border-primary/20 text-xs text-text-primary">
              {quickApplyMsg}
            </div>
          )}
        </div>

        {/* Browser Window Controls Card */}
        <div className="fluent-card p-5 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center gap-2 pb-2 border-b border-border">
              <Globe className="w-4 h-4 text-primary" />
              <h3 className="text-sm font-semibold text-text-primary">Browser Window Control</h3>
            </div>
            <p className="text-xs text-text-muted mt-2 leading-relaxed">
              Launch or close the persistent Playwright browser instance on your Windows desktop.
            </p>
          </div>

          <div className="space-y-2">
            <button
              onClick={() => launchDesktopBrowser.mutate()}
              disabled={launchDesktopBrowser.isPending}
              className="fluent-button fluent-button-secondary text-xs w-full py-2 justify-center"
            >
              <Monitor className="w-3.5 h-3.5 text-primary" />
              <span>{launchDesktopBrowser.isPending ? "Opening..." : "Open Browser Window"}</span>
            </button>

            <button
              onClick={() => closeDesktopBrowser.mutate()}
              disabled={closeDesktopBrowser.isPending}
              className="fluent-button fluent-button-secondary text-xs w-full py-2 justify-center text-danger hover:text-danger"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>Close Browser Window</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Interactive Session Control Panel */}
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
            Strict Single Worker • Bounded Concurrency: <strong className="text-text-primary">1</strong>
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
              className="fluent-button fluent-button-primary text-xs py-2 px-4 shadow-sm"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Start Automation Session</span>
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
                  <Play className="w-4 h-4 fill-current" />
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
            <span>Auto-Build Queue (15)</span>
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
            <span>Retry Failures</span>
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
          <Clock className="w-3.5 h-3.5 text-primary" />
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
              User-selectable preference (1.0 to 5.0s delay between application attempts).
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
            Safety & Review Gating Rules
          </h3>

          {/* Human Review Checkpoint */}
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
              <span className="font-semibold text-text-primary block">Human Review Checkpoint</span>
              <p className="text-text-muted mt-0.5 leading-relaxed">
                Prepares each application and halts in "Awaiting Review" before final submission.
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
              <span className="font-semibold text-text-primary block">Skip Duplicate Jobs</span>
              <p className="text-text-muted mt-0.5 leading-relaxed">
                Prevents applying multiple times to identical normalized URLs or company job IDs.
              </p>
            </div>
          </label>

          {/* CAPTCHA / MFA Safety Halt */}
          <label className="flex items-start gap-3 p-3 rounded-lg bg-surfaceHover/40 border border-border cursor-pointer">
            <input
              type="checkbox"
              checked={formData.stop_on_captcha_mfa ?? true}
              onChange={(e) => setFormData({ ...formData, stop_on_captcha_mfa: e.target.checked })}
              className="mt-0.5 accent-primary rounded"
            />
            <div className="text-xs">
              <span className="font-semibold text-text-primary block">Pause & Preserve Session on CAPTCHA / 2FA</span>
              <p className="text-text-muted mt-0.5 leading-relaxed">
                If Cloudflare, hCaptcha, or MFA challenge appears, keeps the desktop browser window open for you to solve.
              </p>
            </div>
          </label>
        </div>
      </form>
    </div>
  );
};
