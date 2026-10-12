import React, { useState, useEffect } from "react";
import { Sliders, Save, CheckCircle2, ShieldAlert, Sparkles, X } from "lucide-react";
import { useJobPreferences, useAppMutations } from "../api/hooks";
import { JobPreferences } from "../types";

export const PreferencesPage: React.FC = () => {
  const { data: prefs, isLoading } = useJobPreferences();
  const { updateJobPreferences } = useAppMutations();

  const [formData, setFormData] = useState<Partial<JobPreferences>>({});
  const [newKeyword, setNewKeyword] = useState("");
  const [newNegKeyword, setNewNegKeyword] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (prefs) {
      setFormData(prefs);
    }
  }, [prefs]);

  if (isLoading) {
    return <div className="p-8 text-center text-text-muted animate-pulse">Loading preferences...</div>;
  }

  // Calculate live normalized weights
  const wSkills = formData.weight_skills ?? 40;
  const wTitle = formData.weight_title ?? 25;
  const wExp = formData.weight_experience ?? 15;
  const wLoc = formData.weight_location ?? 10;
  const wEmp = formData.weight_employment_type ?? 10;
  const totalWeight = wSkills + wTitle + wExp + wLoc + wEmp || 100;

  const normSkills = ((wSkills / totalWeight) * 100).toFixed(1);
  const normTitle = ((wTitle / totalWeight) * 100).toFixed(1);
  const normExp = ((wExp / totalWeight) * 100).toFixed(1);
  const normLoc = ((wLoc / totalWeight) * 100).toFixed(1);
  const normEmp = ((wEmp / totalWeight) * 100).toFixed(1);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await updateJobPreferences.mutateAsync(formData);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddKeyword = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && newKeyword.trim()) {
      e.preventDefault();
      const current = formData.title_keywords || [];
      if (!current.includes(newKeyword.trim())) {
        setFormData({ ...formData, title_keywords: [...current, newKeyword.trim()] });
      }
      setNewKeyword("");
    }
  };

  const handleAddNegKeyword = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && newNegKeyword.trim()) {
      e.preventDefault();
      const current = formData.negative_keywords || [];
      if (!current.includes(newNegKeyword.trim())) {
        setFormData({ ...formData, negative_keywords: [...current, newNegKeyword.trim()] });
      }
      setNewNegKeyword("");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Job Preferences & Fit Scoring</h1>
          <p className="text-xs md:text-sm text-text-muted mt-0.5">
            Configure target titles, mandatory exclusions, and customize weighted fit criteria.
          </p>
        </div>

        <button
          onClick={handleSubmit}
          disabled={updateJobPreferences.isPending}
          className="fluent-button fluent-button-primary text-xs self-start sm:self-auto"
        >
          <Save className="w-3.5 h-3.5" />
          <span>{updateJobPreferences.isPending ? "Saving..." : saved ? "Preferences Saved!" : "Save Preferences"}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Preferences and Keywords */}
        <div className="lg:col-span-2 space-y-6">
          <form onSubmit={handleSubmit} className="fluent-card p-6 space-y-6">
            {/* Preferred Title Keywords */}
            <div>
              <label className="text-xs font-semibold text-text-primary uppercase tracking-wider block mb-1">
                Target Title Keywords (Press Enter to add)
              </label>
              <div className="flex flex-wrap items-center gap-1.5 p-2.5 bg-surface rounded-lg border border-border mt-1 min-h-[44px]">
                {(formData.title_keywords || []).map((kw, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs bg-primary/15 text-primary font-medium"
                  >
                    <span>{kw}</span>
                    <button
                      type="button"
                      onClick={() =>
                        setFormData({
                          ...formData,
                          title_keywords: (formData.title_keywords || []).filter((k) => k !== kw),
                        })
                      }
                      className="hover:text-danger text-text-muted"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
                <input
                  type="text"
                  placeholder="Add target title..."
                  value={newKeyword}
                  onChange={(e) => setNewKeyword(e.target.value)}
                  onKeyDown={handleAddKeyword}
                  className="bg-transparent text-xs text-text-primary outline-hidden flex-1 min-w-[120px]"
                />
              </div>
            </div>

            {/* Negative Excluded Keywords */}
            <div>
              <div className="flex items-center gap-2 mb-1">
                <label className="text-xs font-semibold text-danger uppercase tracking-wider">
                  Mandatory Negative Keywords (Job Marked Ineligible)
                </label>
              </div>
              <div className="flex flex-wrap items-center gap-1.5 p-2.5 bg-surface rounded-lg border border-border mt-1 min-h-[44px]">
                {(formData.negative_keywords || []).map((neg, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs bg-danger/15 text-danger font-medium"
                  >
                    <span>{neg}</span>
                    <button
                      type="button"
                      onClick={() =>
                        setFormData({
                          ...formData,
                          negative_keywords: (formData.negative_keywords || []).filter((k) => k !== neg),
                        })
                      }
                      className="hover:text-danger text-text-muted"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
                <input
                  type="text"
                  placeholder="Add exclusion (e.g. Sales, Marketing)..."
                  value={newNegKeyword}
                  onChange={(e) => setNewNegKeyword(e.target.value)}
                  onKeyDown={handleAddNegKeyword}
                  className="bg-transparent text-xs text-text-primary outline-hidden flex-1 min-w-[140px]"
                />
              </div>
            </div>

            {/* Remote Work & Salary Preferences */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="space-y-3">
                <label className="flex items-center gap-2 text-xs text-text-primary cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.remote_only ?? true}
                    onChange={(e) => setFormData({ ...formData, remote_only: e.target.checked })}
                    className="accent-primary rounded"
                  />
                  <span className="font-medium">Strict Remote-Only Preference</span>
                </label>
                <p className="text-[11px] text-text-muted">
                  When enabled, non-remote / onsite roles will be marked ineligible.
                </p>
              </div>

              <div>
                <label className="text-xs font-medium text-text-secondary">Minimum Target Salary (USD)</label>
                <input
                  type="number"
                  step="5000"
                  value={formData.min_salary || 80000}
                  onChange={(e) => setFormData({ ...formData, min_salary: Number(e.target.value) })}
                  className="fluent-input w-full mt-1"
                />
              </div>
            </div>
          </form>
        </div>

        {/* Right 1 Col: Transparent Fit Scoring Weight Sliders */}
        <div className="space-y-6">
          <div className="fluent-card p-6 space-y-5">
            <div className="flex items-center gap-2 pb-2 border-b border-border">
              <Sliders className="w-4 h-4 text-primary" />
              <h3 className="text-sm font-semibold text-text-primary">Fit Scoring Weights</h3>
            </div>
            <p className="text-xs text-text-muted leading-relaxed">
              Weights are dynamically normalized to 100%. Adjust priorities based on what matters most for your search.
            </p>

            <div className="space-y-4 text-xs">
              {/* Skills */}
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="font-medium text-text-secondary">Skills Match</span>
                  <span className="font-bold text-primary">{normSkills}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={wSkills}
                  onChange={(e) => setFormData({ ...formData, weight_skills: Number(e.target.value) })}
                  className="w-full accent-primary"
                />
              </div>

              {/* Title */}
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="font-medium text-text-secondary">Job Title Relevance</span>
                  <span className="font-bold text-primary">{normTitle}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={wTitle}
                  onChange={(e) => setFormData({ ...formData, weight_title: Number(e.target.value) })}
                  className="w-full accent-primary"
                />
              </div>

              {/* Experience */}
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="font-medium text-text-secondary">Experience Compatibility</span>
                  <span className="font-bold text-primary">{normExp}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={wExp}
                  onChange={(e) => setFormData({ ...formData, weight_experience: Number(e.target.value) })}
                  className="w-full accent-primary"
                />
              </div>

              {/* Location */}
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="font-medium text-text-secondary">Location & Work Mode</span>
                  <span className="font-bold text-primary">{normLoc}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={wLoc}
                  onChange={(e) => setFormData({ ...formData, weight_location: Number(e.target.value) })}
                  className="w-full accent-primary"
                />
              </div>

              {/* Employment Type */}
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="font-medium text-text-secondary">Employment Type</span>
                  <span className="font-bold text-primary">{normEmp}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={wEmp}
                  onChange={(e) => setFormData({ ...formData, weight_employment_type: Number(e.target.value) })}
                  className="w-full accent-primary"
                />
              </div>
            </div>

            <div className="pt-3 border-t border-border flex items-center justify-between text-xs text-text-muted">
              <span>Normalized Total:</span>
              <span className="font-bold text-success">100.0%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
