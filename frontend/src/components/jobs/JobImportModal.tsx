import React, { useState } from "react";
import { X, Link2, Upload, FileSpreadsheet, CheckCircle2 } from "lucide-react";
import { useAppMutations } from "../../api/hooks";

interface JobImportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const JobImportModal: React.FC<JobImportModalProps> = ({ isOpen, onClose }) => {
  const [tab, setTab] = useState<"url" | "csv">("url");
  const { importJobUrl, importCsv } = useAppMutations();

  // URL Form State
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [location, setLocation] = useState("Remote");
  const [workMode, setWorkMode] = useState("remote");
  const [url, setUrl] = useState("");
  const [skills, setSkills] = useState("");
  const [description, setDescription] = useState("");
  const [salaryMin, setSalaryMin] = useState<number | undefined>();
  const [salaryMax, setSalaryMax] = useState<number | undefined>();

  // CSV State
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [statusMsg, setStatusMsg] = useState("");

  if (!isOpen) return null;

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !company || !url) {
      setStatusMsg("Please provide Title, Company, and URL.");
      return;
    }

    try {
      await importJobUrl.mutateAsync({
        title,
        company,
        location,
        work_mode: workMode,
        employment_type: "full_time",
        original_url: url,
        required_skills: skills.split(",").map((s) => s.trim()).filter(Boolean),
        description,
        salary_min: salaryMin,
        salary_max: salaryMax,
        application_method: "EXTERNAL_SITE",
      });
      setStatusMsg("Job successfully imported!");
      setTimeout(() => {
        onClose();
        setStatusMsg("");
      }, 1000);
    } catch (err: any) {
      setStatusMsg(`Import error: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleCsvSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvFile) {
      setStatusMsg("Please select a CSV file.");
      return;
    }

    try {
      const res = await importCsv.mutateAsync(csvFile);
      setStatusMsg(`Imported ${res.imported_count} jobs (${res.duplicates_skipped} duplicates skipped).`);
      setTimeout(() => {
        onClose();
        setStatusMsg("");
      }, 1500);
    } catch (err: any) {
      setStatusMsg(`CSV error: ${err.response?.data?.detail || err.message}`);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
      <div className="fluent-card w-full max-w-xl bg-surface border-border p-6 shadow-2xl relative">
        <div className="flex items-center justify-between pb-4 border-b border-border">
          <h3 className="text-base font-semibold text-text-primary">Import Job Listings</h3>
          <button onClick={onClose} className="p-1 text-text-muted hover:text-text-primary">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 pt-4 border-b border-border">
          <button
            onClick={() => setTab("url")}
            className={`flex items-center gap-2 pb-2 text-sm font-medium border-b-2 transition-colors ${
              tab === "url"
                ? "border-primary text-primary"
                : "border-transparent text-text-secondary hover:text-text-primary"
            }`}
          >
            <Link2 className="w-4 h-4" />
            <span>Single Job URL</span>
          </button>
          <button
            onClick={() => setTab("csv")}
            className={`flex items-center gap-2 pb-2 text-sm font-medium border-b-2 transition-colors ${
              tab === "csv"
                ? "border-primary text-primary"
                : "border-transparent text-text-secondary hover:text-text-primary"
            }`}
          >
            <FileSpreadsheet className="w-4 h-4" />
            <span>Bulk CSV Import</span>
          </button>
        </div>

        {statusMsg && (
          <div className="mt-3 p-2.5 rounded-lg bg-primary/10 border border-primary/20 text-xs text-text-primary">
            {statusMsg}
          </div>
        )}

        {/* URL Form */}
        {tab === "url" ? (
          <form onSubmit={handleUrlSubmit} className="pt-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-text-secondary">Job Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Senior Backend Engineer"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="fluent-input w-full mt-1"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-text-secondary">Company *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Stripe, Acme Corp"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  className="fluent-input w-full mt-1"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-text-secondary">Work Mode</label>
                <select
                  value={workMode}
                  onChange={(e) => setWorkMode(e.target.value)}
                  className="fluent-input w-full mt-1"
                >
                  <option value="remote">Remote</option>
                  <option value="hybrid">Hybrid</option>
                  <option value="onsite">Onsite</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-text-secondary">Location</label>
                <input
                  type="text"
                  placeholder="e.g. San Francisco, CA / Remote"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="fluent-input w-full mt-1"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-text-secondary">Original Job / Apply URL *</label>
              <input
                type="url"
                required
                placeholder="https://..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="fluent-input w-full mt-1"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-text-secondary">Required Skills (comma separated)</label>
              <input
                type="text"
                placeholder="Python, FastAPI, Docker, SQL"
                value={skills}
                onChange={(e) => setSkills(e.target.value)}
                className="fluent-input w-full mt-1"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-text-secondary">Job Description / Requirements</label>
              <textarea
                rows={3}
                placeholder="Paste key job requirements or summary..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="fluent-input w-full mt-1 text-xs"
              />
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <button type="button" onClick={onClose} className="fluent-button fluent-button-secondary text-xs">
                Cancel
              </button>
              <button
                type="submit"
                disabled={importJobUrl.isPending}
                className="fluent-button fluent-button-primary text-xs"
              >
                {importJobUrl.isPending ? "Importing..." : "Add Job"}
              </button>
            </div>
          </form>
        ) : (
          /* CSV Form */
          <form onSubmit={handleCsvSubmit} className="pt-4 space-y-4">
            <p className="text-xs text-text-muted leading-relaxed">
              Upload a standard CSV file with columns: <code className="text-primary">title</code>,{" "}
              <code className="text-primary">company</code>, <code className="text-primary">location</code>,{" "}
              <code className="text-primary">skills</code>, <code className="text-primary">url</code>. Duplicate
              jobs will automatically be detected and handled per your settings.
            </p>

            <div className="border-2 border-dashed border-border rounded-xl p-6 text-center hover:border-primary/50 transition-colors">
              <Upload className="w-8 h-8 mx-auto text-text-muted mb-2" />
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                className="text-xs text-text-secondary file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-primary file:text-slate-900 cursor-pointer"
              />
              {csvFile && (
                <div className="mt-2 text-xs text-success font-medium flex items-center justify-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Selected: {csvFile.name} ({(csvFile.size / 1024).toFixed(1)} KB)
                </div>
              )}
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <button type="button" onClick={onClose} className="fluent-button fluent-button-secondary text-xs">
                Cancel
              </button>
              <button
                type="submit"
                disabled={!csvFile || importCsv.isPending}
                className="fluent-button fluent-button-primary text-xs"
              >
                {importCsv.isPending ? "Uploading..." : "Import CSV Listings"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
