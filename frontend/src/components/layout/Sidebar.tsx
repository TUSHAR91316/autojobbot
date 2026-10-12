import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Search,
  ListOrdered,
  History,
  User,
  Sliders,
  PlayCircle,
  FileText,
  Settings as SettingsIcon,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
} from "lucide-react";
import { useQueue, useExternalQueue } from "../../api/hooks";

interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (v: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, setCollapsed }) => {
  const { data: queue = [] } = useQueue();
  const { data: extQueue = [] } = useExternalQueue();
  const totalQueue = queue.length + extQueue.length;

  const navItems = [
    { to: "/", label: "Dashboard", icon: LayoutDashboard },
    { to: "/jobs", label: "Find Jobs", icon: Search },
    {
      to: "/queue",
      label: "Application Queue",
      icon: ListOrdered,
      badge: totalQueue > 0 ? totalQueue : undefined,
    },
    { to: "/history", label: "Application History", icon: History },
    { to: "/profile", label: "Resume & Profile", icon: User },
    { to: "/preferences", label: "Job Preferences", icon: Sliders },
    { to: "/automation", label: "Automation", icon: PlayCircle },
    { to: "/logs", label: "Activity Logs", icon: FileText },
    { to: "/settings", label: "Settings", icon: SettingsIcon },
  ];

  return (
    <aside
      className={`fixed top-0 left-0 bottom-0 z-30 flex flex-col bg-surface border-r border-border transition-all duration-300 ${
        collapsed ? "w-16" : "w-64"
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-border">
        {!collapsed && (
          <div className="flex items-center gap-2 overflow-hidden">
            <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold text-lg shadow-sm">
              <ShieldCheck className="w-5 h-5 text-primary" />
            </div>
            <div className="truncate">
              <span className="font-semibold text-text-primary tracking-tight text-base block">
                ApplyPilot
              </span>
              <span className="text-[10px] text-text-muted block font-medium -mt-1">
                Local Assistant
              </span>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="mx-auto w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary">
            <ShieldCheck className="w-5 h-5 text-primary" />
          </div>
        )}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className={`p-1.5 rounded-md text-text-secondary hover:text-text-primary hover:bg-surfaceHover transition-colors ${
            collapsed ? "hidden" : ""
          }`}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>

      {/* Nav List */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary/15 text-primary font-semibold shadow-xs"
                    : "text-text-secondary hover:text-text-primary hover:bg-surfaceHover"
                } ${collapsed ? "justify-center px-2" : ""}`
              }
              title={collapsed ? item.label : undefined}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {!collapsed && <span className="truncate flex-1">{item.label}</span>}
              {!collapsed && item.badge !== undefined && (
                <span className="px-1.5 py-0.5 text-xs font-semibold rounded-full bg-primary/20 text-primary">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer / Toggle for collapsed state */}
      {collapsed && (
        <div className="p-2 border-t border-border flex justify-center">
          <button
            onClick={() => setCollapsed(false)}
            className="p-1.5 rounded-md text-text-secondary hover:text-text-primary hover:bg-surfaceHover"
            title="Expand sidebar"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </aside>
  );
};
