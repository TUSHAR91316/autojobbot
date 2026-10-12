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
  const { discoverJobs, startAutomation, pauseAutomation, resumeAutomation, stopAutomation, toggleSimulationMode } = useAppMutations();
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
        {/* Live Browser / Simulation Mode Toggle Badge */}
        <button
          onClick={() => toggleSimulationMode.mutate()}
          disabled={toggleSimulationMode.isPending}
          className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border transition-all cursor-pointer ${
            status?.simulation_mode
              ? "bg-warning/15 border-warning/40 text-warning hover:bg-warning/25"
              : "bg-success/15 border-success/40 text-success hover:bg-success/25"
          }`}
          title="Click to toggle between Live Desktop Browser (Real Chrome) and Simulation Mode"
        >
          <span className={`w-2 h-2 rounded-full ${status?.simulation_mode ? "bg-warning" : "bg-success"} animate-pulse`} />
          <span>{status?.simulation_mode ? "Dry Run Simulation" : "Live Desktop Browser"}</span>
        </button>

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

        {/* Discover Live Jobs Button */}
        <button
          onClick={() => discoverJobs.mutate("all")}
          disabled={discoverJobs.isPending}
          className="fluent-button fluent-button-secondary text-xs py-1.5 px-3 hidden md:inline-flex"
          title="Search live job feeds"
        >
          <Sparkles className="w-3.5 h-3.5 text-primary" />
          <span>{discoverJobs.isPending ? "Searching..." : "Discover Jobs"}</span>
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
