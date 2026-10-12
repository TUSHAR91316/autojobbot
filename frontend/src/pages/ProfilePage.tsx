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
  Code,
  FileCode,
  Eye,
  File,
  Copy,
  Check,
} from "lucide-react";
import { useProfile, useResumes, useAppMutations } from "../api/hooks";
import { CandidateProfile, ResumeVersion } from "../types";

export const ProfilePage: React.FC = () => {
  const { data: profile, isLoading } = useProfile();
  const { data: resumes = [] } = useResumes();
  const { updateProfile, uploadResume, pasteResume, setPrimaryResume, deleteResume } = useAppMutations();

  // Local form state
  const [formData, setFormData] = useState<Partial<CandidateProfile>>({});
  const [newSkill, setNewSkill] = useState("");
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Resume creation tab: "upload" | "paste"
  const [resumeMode, setResumeMode] = useState<"upload" | "paste">("upload");
  const [resumeLabel, setResumeLabel] = useState("");
  const [resumeCategories, setResumeCategories] = useState("");
  const [isPrimaryUpload, setIsPrimaryUpload] = useState(false);
  const [resumeFile, setResumeFile] = useState<File | null>(null);

  // Direct paste state
  const [pastedFormat, setPastedFormat] = useState<"tex" | "txt">("tex");
  const [pastedContent, setPastedContent] = useState("");
  const [actionMsg, setActionMsg] = useState("");

  // Inspect modal
  const [previewResume, setPreviewResume] = useState<ResumeVersion | null>(null);
  const [copiedText, setCopiedText] = useState(false);

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

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resumeFile || !resumeLabel.trim()) {
      setActionMsg("Please provide a label and select a file.");
      return;
    }

    try {
      setActionMsg("");
      const fd = new FormData();
      fd.append("label", resumeLabel.trim());
      fd.append("target_categories", resumeCategories);
      fd.append("is_primary", isPrimaryUpload ? "true" : "false");
      fd.append("file", resumeFile);

      await uploadResume.mutateAsync(fd);
      setResumeFile(null);
      setResumeLabel("");
      setResumeCategories("");
      setIsPrimaryUpload(false);
      setActionMsg("Resume uploaded and parsed successfully!");
      setTimeout(() => setActionMsg(""), 2500);
    } catch (err: any) {
      setActionMsg(err.response?.data?.detail || "Failed to upload resume file");
    }
  };

  const handleDirectPaste = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resumeLabel.trim() || !pastedContent.trim()) {
      setActionMsg("Please provide a label and paste resume content.");
      return;
    }

    try {
      setActionMsg("");
      const cats = resumeCategories.split(",").map((c) => c.trim()).filter(Boolean);
      await pasteResume.mutateAsync({
        label: resumeLabel.trim(),
        target_categories: cats,
        is_primary: isPrimaryUpload,
        file_type: pastedFormat,
        content: pastedContent.trim(),
      });
      setResumeLabel("");
      setResumeCategories("");
      setPastedContent("");
      setIsPrimaryUpload(false);
      setActionMsg("Resume created and parsed successfully!");
      setTimeout(() => setActionMsg(""), 2500);
    } catch (err: any) {
      setActionMsg(err.response?.data?.detail || "Failed to save resume");
    }
  };

  const getFormatBadge = (fileType: string) => {
    const ft = (fileType || "").toLowerCase().replace(".", "");
    if (ft === "pdf") {
      return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-danger/15 text-danger">PDF</span>;
    } else if (ft === "docx" || ft === "doc") {
      return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-primary/15 text-primary">WORD</span>;
    } else if (ft === "tex" || ft === "latex") {
      return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-success/15 text-success">LATEX</span>;
    } else {
      return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-warning/15 text-warning">TEXT</span>;
    }
  };

  const handleCopyExtracted = () => {
    if (previewResume) {
      navigator.clipboard.writeText(previewResume.extracted_text || "");
      setCopiedText(true);
      setTimeout(() => setCopiedText(false), 2000);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Candidate Profile & Resumes</h1>
          <p className="text-xs md:text-sm text-text-muted mt-0.5">
            Truthful profile credentials supporting <strong>LaTeX (.tex)</strong>, <strong>PDF</strong>, <strong>Word (.docx)</strong>, and <strong>Text (.txt, .md)</strong>.
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
            <div className="flex items-center justify-between pb-2 border-b border-border flex-wrap gap-2">
              <h2 className="text-sm font-semibold text-text-primary uppercase tracking-wider">
                Personal & Contact Information
              </h2>
              <button
                type="button"
                onClick={() =>
                  setFormData({
                    ...formData,
                    current_location: "Bengaluru, India",
                    preferred_locations: ["India", "Bengaluru", "Hyderabad", "Pune", "Mumbai", "Delhi NCR", "Remote - India"],
                    salary_currency: "INR",
                    remote_preference: "any",
                  })
                }
                className="px-2.5 py-1 rounded-md text-xs font-semibold bg-success/15 border border-success/30 text-success hover:bg-success/25 transition-colors flex items-center gap-1.5 cursor-pointer"
                title="Automatically configure candidate profile for India Tech Hubs"
              >
                <span>🇮🇳 Preset: India Tech Hubs (Bengaluru / Remote)</span>
              </button>
            </div>

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
                <label className="text-xs font-medium text-text-secondary">Current Location (Real-time Apply Preference)</label>
                <input
                  type="text"
                  value={formData.current_location || ""}
                  onChange={(e) => setFormData({ ...formData, current_location: e.target.value })}
                  placeholder="e.g. Bengaluru, India"
                  className="fluent-input w-full mt-1"
                />
                {/* Location Quick Chips */}
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {["Bengaluru, India", "Hyderabad, India", "Pune, India", "Mumbai, India", "Delhi NCR, India", "Remote - India"].map((loc) => (
                    <button
                      key={loc}
                      type="button"
                      onClick={() => setFormData({ ...formData, current_location: loc })}
                      className="px-1.5 py-0.5 rounded text-[10px] bg-surfaceHover text-text-muted hover:text-text-primary hover:bg-primary/10 transition-colors"
                    >
                      {loc}
                    </button>
                  ))}
                </div>
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

        {/* Right 1 Column: Resumes Management with LaTeX, Word, PDF, Text */}
        <div className="space-y-6">
          <div className="fluent-card p-5 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-border">
              <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" />
                <span>Add Resume Version</span>
              </h3>
            </div>

            {/* Supported Formats Banner */}
            <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
              <span className="text-text-muted">Supported:</span>
              <span className="px-1.5 py-0.2 rounded bg-danger/10 text-danger font-semibold">PDF</span>
              <span className="px-1.5 py-0.2 rounded bg-primary/10 text-primary font-semibold">Word (.docx)</span>
              <span className="px-1.5 py-0.2 rounded bg-success/10 text-success font-semibold">LaTeX (.tex)</span>
              <span className="px-1.5 py-0.2 rounded bg-warning/10 text-warning font-semibold">Text (.txt, .md)</span>
            </div>

            {/* Mode Selector Tabs */}
            <div className="grid grid-cols-2 gap-1 p-1 bg-surfaceHover/50 rounded-lg border border-border text-xs">
              <button
                type="button"
                onClick={() => setResumeMode("upload")}
                className={`py-1.5 rounded-md font-medium transition-all flex items-center justify-center gap-1.5 ${
                  resumeMode === "upload"
                    ? "bg-primary text-slate-900 font-semibold shadow-xs"
                    : "text-text-secondary hover:text-text-primary"
                }`}
              >
                <Upload className="w-3.5 h-3.5" />
                <span>Upload File</span>
              </button>
              <button
                type="button"
                onClick={() => setResumeMode("paste")}
                className={`py-1.5 rounded-md font-medium transition-all flex items-center justify-center gap-1.5 ${
                  resumeMode === "paste"
                    ? "bg-primary text-slate-900 font-semibold shadow-xs"
                    : "text-text-secondary hover:text-text-primary"
                }`}
              >
                <Code className="w-3.5 h-3.5" />
                <span>Paste LaTeX / Text</span>
              </button>
            </div>

            {actionMsg && (
              <div className="p-2 rounded bg-primary/10 border border-primary/20 text-xs text-text-primary">
                {actionMsg}
              </div>
            )}

            {/* Form Mode 1: File Upload */}
            {resumeMode === "upload" ? (
              <form onSubmit={handleFileUpload} className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-text-secondary">Version Label *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Lead_LaTeX_2026 or FullStack_PDF"
                    value={resumeLabel}
                    onChange={(e) => setResumeLabel(e.target.value)}
                    className="fluent-input w-full mt-1 text-xs"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-text-secondary">Target Categories (comma separated)</label>
                  <input
                    type="text"
                    placeholder="Backend, Python, Full Stack"
                    value={resumeCategories}
                    onChange={(e) => setResumeCategories(e.target.value)}
                    className="fluent-input w-full mt-1 text-xs"
                  />
                </div>

                <div className="border border-dashed border-border rounded-lg p-3 text-center hover:border-primary/50 transition-colors">
                  <input
                    type="file"
                    accept=".pdf,.docx,.doc,.tex,.txt,.md"
                    onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
                    className="text-xs text-text-secondary file:mr-2 file:py-1 file:px-2.5 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-surfaceHover file:text-text-primary cursor-pointer"
                  />
                  {resumeFile && (
                    <span className="text-[11px] text-success block mt-1.5 font-medium">
                      Selected: {resumeFile.name} ({(resumeFile.size / 1024).toFixed(1)} KB)
                    </span>
                  )}
                  <span className="text-[10px] text-text-muted block mt-1">
                    Accepts .pdf, .docx, .doc, .tex (LaTeX), .txt, .md
                  </span>
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
                  disabled={uploadResume.isPending || !resumeFile}
                  className="fluent-button fluent-button-primary text-xs w-full py-2"
                >
                  {uploadResume.isPending ? "Extracting & Saving..." : "Upload & Parse Resume"}
                </button>
              </form>
            ) : (
              /* Form Mode 2: Direct Paste (LaTeX or Plain Text) */
              <form onSubmit={handleDirectPaste} className="space-y-3">
                <div className="flex gap-2">
                  <div className="flex-1">
                    <label className="text-xs font-medium text-text-secondary">Version Label *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. My_LaTeX_Source"
                      value={resumeLabel}
                      onChange={(e) => setResumeLabel(e.target.value)}
                      className="fluent-input w-full mt-1 text-xs"
                    />
                  </div>

                  <div className="w-32">
                    <label className="text-xs font-medium text-text-secondary">Format</label>
                    <select
                      value={pastedFormat}
                      onChange={(e) => setPastedFormat(e.target.value as "tex" | "txt")}
                      className="fluent-input w-full mt-1 text-xs"
                    >
                      <option value="tex">LaTeX (.tex)</option>
                      <option value="txt">Plain Text / MD</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium text-text-secondary">Target Categories</label>
                  <input
                    type="text"
                    placeholder="e.g. Systems Engineer, AI"
                    value={resumeCategories}
                    onChange={(e) => setResumeCategories(e.target.value)}
                    className="fluent-input w-full mt-1 text-xs"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-text-secondary flex justify-between items-center">
                    <span>{pastedFormat === "tex" ? "Paste LaTeX Source Code *" : "Paste Plain Text Resume *"}</span>
                    <span className="text-[10px] text-text-muted">Parser strips preamble & tags</span>
                  </label>
                  <textarea
                    rows={7}
                    required
                    placeholder={
                      pastedFormat === "tex"
                        ? "\\begin{document}\n\\textbf{My Name}\n\\section{Experience}...\n\\end{document}"
                        : "John Doe\nSoftware Engineer\nExperience: Senior Developer at Acme..."
                    }
                    value={pastedContent}
                    onChange={(e) => setPastedContent(e.target.value)}
                    className="fluent-input w-full mt-1 font-mono text-xs leading-relaxed"
                  />
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
                  disabled={pasteResume.isPending || !pastedContent.trim()}
                  className="fluent-button fluent-button-primary text-xs w-full py-2"
                >
                  {pasteResume.isPending ? "Parsing..." : `Save & Parse ${pastedFormat.toUpperCase()} Resume`}
                </button>
              </form>
            )}
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
                    <div className="space-y-1 overflow-hidden">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <FileText className="w-3.5 h-3.5 text-primary shrink-0" />
                        <span className="text-xs font-semibold text-text-primary truncate">{r.label}</span>
                        {getFormatBadge(r.file_type)}
                        {r.is_primary && (
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-success/20 text-success">
                            PRIMARY
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-text-muted">
                        {(r.file_size / 1024).toFixed(1)} KB • {r.file_name}
                      </div>
                    </div>

                    <div className="flex items-center gap-1 shrink-0">
                      {/* Inspect Extracted Text */}
                      <button
                        onClick={() => setPreviewResume(r)}
                        className="p-1 text-text-muted hover:text-text-primary rounded hover:bg-surfaceHover"
                        title="Inspect extracted clean text"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>

                      {!r.is_primary && (
                        <button
                          onClick={() => setPrimaryResume.mutate(r.id)}
                          className="p-1 text-text-muted hover:text-warning rounded hover:bg-surfaceHover"
                          title="Set as primary"
                        >
                          <Star className="w-3.5 h-3.5" />
                        </button>
                      )}
                      <button
                        onClick={() => deleteResume.mutate(r.id)}
                        className="p-1 text-text-muted hover:text-danger rounded hover:bg-surfaceHover"
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

      {/* Extracted Text Preview Modal */}
      {previewResume && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="fluent-card w-full max-w-2xl bg-surface border-border p-6 shadow-2xl relative max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" />
                <h3 className="text-sm font-semibold text-text-primary">
                  Extracted Text: {previewResume.label}
                </h3>
                {getFormatBadge(previewResume.file_type)}
              </div>
              <button
                onClick={() => setPreviewResume(null)}
                className="p-1 text-text-muted hover:text-text-primary rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="py-2 text-xs text-text-muted flex justify-between items-center">
              <span>This is the clean text extracted locally for scoring and application preparation.</span>
              <button
                onClick={handleCopyExtracted}
                className="fluent-button fluent-button-secondary text-[11px] py-1 px-2.5"
              >
                {copiedText ? <Check className="w-3 h-3 text-success" /> : <Copy className="w-3 h-3" />}
                <span>{copiedText ? "Copied" : "Copy"}</span>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto mt-2 p-3 bg-surfaceHover/50 rounded-lg border border-border">
              <pre className="text-xs font-mono text-text-primary whitespace-pre-wrap leading-relaxed select-all">
                {previewResume.extracted_text || "(No extracted text available)"}
              </pre>
            </div>

            <div className="pt-3 border-t border-border mt-3 flex justify-end">
              <button
                onClick={() => setPreviewResume(null)}
                className="fluent-button fluent-button-secondary text-xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
