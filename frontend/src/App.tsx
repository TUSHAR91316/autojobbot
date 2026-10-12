import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Sidebar } from "./components/layout/Sidebar";
import { Header } from "./components/layout/Header";
import { DashboardPage } from "./pages/DashboardPage";
import { FindJobsPage } from "./pages/FindJobsPage";
import { QueuePage } from "./pages/QueuePage";
import { HistoryPage } from "./pages/HistoryPage";
import { ProfilePage } from "./pages/ProfilePage";
import { PreferencesPage } from "./pages/PreferencesPage";
import { AutomationPage } from "./pages/AutomationPage";
import { LogsPage } from "./pages/LogsPage";
import { SettingsPage } from "./pages/SettingsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5000,
    },
  },
});

export const App: React.FC = () => {
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    return (localStorage.getItem("applypilot_theme") as "dark" | "light") || "dark";
  });
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    document.documentElement.classList.remove("dark", "light");
    document.documentElement.classList.add(theme);
    localStorage.setItem("applypilot_theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-background text-text-primary flex">
          {/* Collapsible Sidebar */}
          <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />

          {/* Main Area */}
          <div
            className={`flex-1 min-h-screen flex flex-col transition-all duration-300 ${
              collapsed ? "pl-16" : "pl-64"
            }`}
          >
            {/* Top Navigation */}
            <Header theme={theme} toggleTheme={toggleTheme} collapsed={collapsed} />

            {/* Main Page Content */}
            <main className="flex-1 pt-20 px-4 sm:px-8 pb-12 max-w-7xl w-full mx-auto">
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/jobs" element={<FindJobsPage />} />
                <Route path="/queue" element={<QueuePage />} />
                <Route path="/history" element={<HistoryPage />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/preferences" element={<PreferencesPage />} />
                <Route path="/automation" element={<AutomationPage />} />
                <Route path="/logs" element={<LogsPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
