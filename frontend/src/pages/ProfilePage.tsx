import React, { useState, useEffect } from "react";
import {
  User,
  Upload,
  FileText,
  Star,
  Trash2,
  CheckCircle2,
  Plus,
  X,
  ExternalLink,
  Save,
  Briefcase,
  GraduationCap,
} from "lucide-react";
import { useProfile, useResumes, useAppMutations } from "../api/hooks";
import { CandidateProfile } from "../types";

export const ProfilePage: React.FC = () => {
  const { data: profile, isLoading } = useProfile();
  const { data: resumes = [] } = useResumes();
  const { updateProfile, uploadResume, setPrimaryResume, deleteResume } = useAppMutations();

  // Local form state
  const [formData, setFormData] = useState<Partial<CandidateProfile>>({});
  const [newSkill, setNewSkill] = useState("");
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Resume upload state
  const [resumeLabel, setResumeLabel] = useState("");
  const [resumeCategories, setResumeCategories] = useState("");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [isPrimaryUpload, setIsPrimaryUpload] = useState(false);
  const [uploadError, setUploadError] = useState("");

  useEffect(() => {
    if (profile) {
      setFormData(profile);
    }
  }, [profile]);

  if (isLoading) {
    return <div className="p-8 text-center text-text-muted animate-pulse">Loading profile...</div>;
  }

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await updateProfile.mutateAsync(formData);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddSkill = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && newSkill.trim()) {
      e.preventDefault();
      const currentSkills = formData.skills || [];
      if (!currentSkills.includes(newSkill.trim())) {
        setFormData({ ...formData, skills: [...currentSkills, newSkill.trim()] });
      }
      setNewSkill("");
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setFormData({
      ...formData,
      skills: (formData.skills || []).filter((s) => s !== skillToRemove),
    });
  };

  const handleResumeUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resumeFile || !resumeLabel) {
      setUploadError("Please provide a label and select a PDF or DOCX file.");
      return;
    }

    try {
      setUploadError("");
      const fd = new FormData();
      fd.append("label", resumeLabel);
      fd.append("target_categories", resumeCategories);
      fd.append("is_primary", isPrimaryUpload ? "true" : "false");
      fd.append("file", resumeFile);

      await uploadResume.mutateAsync(fd);
      setResumeFile(null);
      setResumeLabel("");
      setResumeCategories("");
      setIsPrimaryUpload(false);
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || "Failed to upload resume");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Candidate Profile & Resumes</h1>
          <p className="text-xs md:text-sm text-text-muted mt-0.5">
            Truthful profile credentials used to evaluate jobs and populate applications without hallucination.
          </p>
        </div>

        <button
          onClick={handleProfileSubmit}
          disabled={updateProfile.isPending}
          className="fluent-button fluent-button-primary text-xs self-start sm:self-auto"
        >
          <Save className="w-3.5 h-3.5" />
          <span>{updateProfile.isPending ? "Saving..." : saveSuccess ? "Saved Successfully!" : "Save Profile"}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns: Profile Details Form */}
        <div className="lg:col-span-2 space-y-6">
          <form onSubmit={handleProfileSubmit} className="fluent-card p-6 space-y-5">
            <h2 className="text-sm font-semibold text-text-primary uppercase tracking-wider pb-2 border-b border-border">
              Personal & Contact Information
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-text-secondary">Full Name *</label>
                <input
                  type="text"
                  required
                  value={formData.full_name || ""}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="fluent-input w-full mt-1"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-text-secondary">Email Address *</label>
                <input
                  type="email"
                  required
                  value={formData.email || ""}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="fluent-input w-full mt-1"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-text-secondary">Phone Number</label>
                <input
                  type="tel"
                  value={formData.phone || ""}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="fluent-input w-full mt-1"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-text-secondary">Current Location</label>
                <input
                  type="text"
                  value={formData.current_location || ""}
                  onChange={(e) => setFormData({ ...formData, current_location: e.target.value })}
                  className="fluent-input w-full mt-1"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-text-secondary">Professional Headline</label>
              <input
                type="text"
                placeholder="e.g. Senior Full Stack Engineer | Python & React"
                value={formData.headline || ""}
                onChange={(e) => setFormData({ ...formData, headline: e.target.value })}
                className="fluent-input w-full mt-1"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-text-secondary">Professional Summary</label>
              <textarea
                rows={3}
                value={formData.summary || ""}
                onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
                className="fluent-input w-full mt-1 text-xs"
              />
            </div>

            {/* Skills Tags */}
            <div>
              <label className="text-xs font-medium text-text-secondary">Core Skills (Press Enter to add)</label>
              <div className="flex flex-wrap items-center gap-1.5 p-2 bg-surface rounded-lg border border-border mt-1 min-h-[44px]">
                {(formData.skills || []).map((skill, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-primary/15 text-primary font-medium"
                  >
                    <span>{skill}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveSkill(skill)}
                      className="hover:text-danger text-text-muted transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
                <input
                  type="text"
                  placeholder="Add skill..."
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyDown={handleAddSkill}
                  className="bg-transparent text-xs text-text-primary outline-hidden flex-1 min-w-[80px]"
                />
              </div>
            </div>

            {/* Online Links */}
            <h2 className="text-sm font-semibold text-text-primary uppercase tracking-wider pt-4 pb-2 border-b border-border">
              Online Profiles & Links
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-xs font-medium text-text-secondary">Portfolio URL</label>
                <input
                  type="url"
                  placeholder="https://mywebsite.com"
                  value={formData.portfolio_url || ""}
                  onChange={(e) => setFormData({ ...formData, portfolio_url: e.target.value })}
                  className="fluent-input w-full mt-1 text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-text-secondary">GitHub URL</label>
                <input
                  type="url"
                  placeholder="https://github.com/username"
                  value={formData.github_url || ""}
                  onChange={(e) => setFormData({ ...formData, github_url: e.target.value })}
                  className="fluent-input w-full mt-1 text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-text-secondary">LinkedIn URL</label>
                <input
                  type="url"
                  placeholder="https://linkedin.com/in/username"
                  value={formData.linkedin_url || ""}
                  onChange={(e) => setFormData({ ...formData, linkedin_url: e.target.value })}
                  className="fluent-input w-full mt-1 text-xs"
                />
              </div>
            </div>

            {/* Experience & Seniority */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="text-xs font-medium text-text-secondary">Years of Experience</label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  max="40"
                  value={formData.years_of_experience || 0}
                  onChange={(e) => setFormData({ ...formData, years_of_experience: Number(e.target.value) })}
                  className="fluent-input w-full mt-1"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-text-secondary">Seniority Level</label>
                <select
                  value={formData.experience_level || "mid"}
                  onChange={(e) => setFormData({ ...formData, experience_level: e.target.value })}
                  className="fluent-input w-full mt-1"
                >
                  <option value="entry">Entry Level (0-2 years)</option>
                  <option value="mid">Mid Level (2-5 years)</option>
                  <option value="senior">Senior Level (5-8 years)</option>
                  <option value="lead">Lead / Principal (8+ years)</option>
                </select>
              </div>
            </div>
          </form>
        </div>

        {/* Right 1 Column: Resumes Management */}
        <div className="space-y-6">
          {/* Upload Resume Form */}
          <div className="fluent-card p-5 space-y-4">
            <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
              <Upload className="w-4 h-4 text-primary" />
              <span>Upload Resume Version</span>
            </h3>

            {uploadError && (
              <div className="p-2 rounded bg-danger/10 border border-danger/20 text-xs text-danger">
                {uploadError}
              </div>
            )}

            <form onSubmit={handleResumeUpload} className="space-y-3">
              <div>
                <label className="text-xs font-medium text-text-secondary">Version Label *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Lead_Python_2026"
                  value={resumeLabel}
                  onChange={(e) => setResumeLabel(e.target.value)}
                  className="fluent-input w-full mt-1 text-xs"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-text-secondary">Target Categories (comma separated)</label>
                <input
                  type="text"
                  placeholder="Full Stack, Backend, Python"
                  value={resumeCategories}
                  onChange={(e) => setResumeCategories(e.target.value)}
                  className="fluent-input w-full mt-1 text-xs"
                />
              </div>

              <div className="border border-dashed border-border rounded-lg p-3 text-center">
                <input
                  type="file"
                  accept=".pdf,.docx"
                  onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
                  className="text-xs text-text-secondary file:mr-2 file:py-1 file:px-2.5 file:rounded file:border-0 file:text-xs file:font-medium file:bg-surfaceHover file:text-text-primary cursor-pointer"
                />
                <span className="text-[11px] text-text-muted block mt-1">PDF or DOCX (Max 10MB)</span>
              </div>

              <label className="flex items-center gap-2 text-xs text-text-secondary cursor-pointer">
                <input
                  type="checkbox"
                  checked={isPrimaryUpload}
                  onChange={(e) => setIsPrimaryUpload(e.target.checked)}
                  className="accent-primary rounded"
                />
                <span>Set as primary default resume</span>
              </label>

              <button
                type="submit"
                disabled={uploadResume.isPending}
                className="fluent-button fluent-button-primary text-xs w-full py-2"
              >
                {uploadResume.isPending ? "Extracting & Saving..." : "Upload & Parse Resume"}
              </button>
            </form>
          </div>

          {/* Stored Resumes List */}
          <div className="fluent-card p-5 space-y-3">
            <h3 className="text-sm font-semibold text-text-primary">Stored Resume Versions ({resumes.length})</h3>

            {resumes.length === 0 ? (
              <p className="text-xs text-text-muted py-4 text-center">No resumes uploaded yet.</p>
            ) : (
              <div className="space-y-2.5">
                {resumes.map((r) => (
                  <div
                    key={r.id}
                    className="p-3 rounded-lg bg-surfaceHover/50 border border-border flex items-start justify-between gap-3"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5">
                        <FileText className="w-4 h-4 text-primary" />
                        <span className="text-xs font-semibold text-text-primary">{r.label}</span>
                        {r.is_primary && (
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-success/20 text-success">
                            PRIMARY
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-text-muted">
                        {r.file_type.toUpperCase()} • {(r.file_size / 1024).toFixed(1)} KB
                      </div>
                    </div>

                    <div className="flex items-center gap-1">
                      {!r.is_primary && (
                        <button
                          onClick={() => setPrimaryResume.mutate(r.id)}
                          className="p-1 text-text-muted hover:text-warning"
                          title="Set as primary"
                        >
                          <Star className="w-3.5 h-3.5" />
                        </button>
                      )}
                      <button
                        onClick={() => deleteResume.mutate(r.id)}
                        className="p-1 text-text-muted hover:text-danger"
                        title="Delete resume"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
