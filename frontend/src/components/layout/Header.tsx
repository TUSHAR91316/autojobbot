import React, { useState } from "react";
import {
  Sun,
  Moon,
  Sparkles,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Play,
  Pause,
  Square,
  Search as SearchIcon,
} from "lucide-react";
import { useAutomationStatus, useAppMutations, useAutomationSettings } from "../../api/hooks";
import { useNavigate } from "react-router-dom";

interface HeaderProps {
  theme: "dark" | "light";
  toggleTheme: () => void;
  collapsed: boolean;
}

export const Header: React.FC<HeaderProps> = ({ theme, toggleTheme, collapsed }) => {
  const { data: status } = useAutomationStatus();
  const { data: settings } = useAutomationSettings();
  const { seedDemoData, startAutomation, pauseAutomation, resumeAutomation, stopAutomation } = useAppMutations();
  const [searchVal, setSearchVal] = useState("");
  const navigate = useNavigate();

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchVal.trim()) {
      navigate(`/jobs?search=${encodeURIComponent(searchVal.trim())}`);
    }
  };

  const isRunning = status?.is_active && !status?.is_paused;
  const isPaused = status?.is_paused;

  return (
    <header
      className={`fixed top-0 right-0 z-20 h-16 flex items-center justify-between px-6 bg-surface/80 backdrop-blur-md border-b border-border transition-all duration-300 ${
        collapsed ? "left-16" : "left-64"
      }`}
    >
      {/* Global Search Bar */}
      <form onSubmit={handleSearchSubmit} className="relative w-72 md:w-96">
        <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
        <input
          type="text"
          placeholder="Search jobs, companies, skills..."
          value={searchVal}
          onChange={(e) => setSearchVal(e.target.value)}
          className="fluent-input w-full pl-9 pr-4 py-1.5 text-xs md:text-sm bg-surfaceHover/50"
        />
      </form>

      {/* Right Controls & Status Pill */}
      <div className="flex items-center gap-3">
        {/* Safe Simulation Mode Badge */}
        <div
          className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
            settings?.simulation_mode
              ? "bg-primary/10 border-primary/30 text-primary"
              : "bg-warning/10 border-warning/30 text-warning"
          }`}
          title={
            settings?.simulation_mode
              ? "Safe Simulation Active: Exercises full pipeline without submitting to real portals"
              : "Live Submission Mode"
          }
        >
          <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
          <span>{settings?.simulation_mode ? "Safe Simulation" : "Live Automation"}</span>
        </div>

        {/* Live Session Controller & Telemetry Pill */}
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-surfaceHover border border-border text-xs">
          <Activity
            className={`w-3.5 h-3.5 ${
              isRunning ? "text-success animate-spin" : isPaused ? "text-warning" : "text-text-muted"
            }`}
          />
          <span className="font-medium text-text-primary">
            {isRunning ? `Running (${status?.submitted_count}/${status?.target_count})` : isPaused ? "Paused" : "Idle"}
          </span>

          {isRunning && (
            <button
              onClick={() => pauseAutomation.mutate()}
              className="p-1 hover:text-warning transition-colors"
              title="Pause automation"
            >
              <Pause className="w-3 h-3" />
            </button>
          )}

          {isPaused && (
            <button
              onClick={() => resumeAutomation.mutate()}
              className="p-1 hover:text-success transition-colors"
              title="Resume automation"
            >
              <Play className="w-3 h-3" />
            </button>
          )}

          {(isRunning || isPaused) && (
            <button
              onClick={() => stopAutomation.mutate()}
              className="p-1 hover:text-danger transition-colors"
              title="Stop immediately"
            >
              <Square className="w-3 h-3" />
            </button>
          )}
        </div>

        {/* Load Demo Data Button */}
        <button
          onClick={() => seedDemoData.mutate()}
          disabled={seedDemoData.isPending}
          className="fluent-button fluent-button-secondary text-xs py-1.5 px-3 hidden md:inline-flex"
          title="Seed realistic demo jobs & queue records"
        >
          <Sparkles className="w-3.5 h-3.5 text-primary" />
          <span>{seedDemoData.isPending ? "Seeding..." : "Load Demo Data"}</span>
        </button>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surfaceHover transition-colors border border-border/50"
          title={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
        >
          {theme === "dark" ? <Sun className="w-4 h-4 text-warning" /> : <Moon className="w-4 h-4 text-primary" />}
        </button>
      </div>
    </header>
  );
};
