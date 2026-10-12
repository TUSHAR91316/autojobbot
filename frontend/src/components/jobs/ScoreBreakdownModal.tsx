import React from "react";
import { X, CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import { JobListing } from "../../types";

interface ScoreBreakdownModalProps {
  job: JobListing | null;
  onClose: () => void;
}

export const ScoreBreakdownModal: React.FC<ScoreBreakdownModalProps> = ({ job, onClose }) => {
  if (!job) return null;

  const bd = job.match_breakdown || {};
  const elig = job.eligibility_assessment || { is_eligible: true, reasons: [] };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="fluent-card w-full max-w-lg bg-surface border-border p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-border">
          <div>
            <h3 className="text-lg font-semibold text-text-primary">{job.title}</h3>
            <p className="text-xs text-text-muted">{job.company} • {job.location}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-text-muted hover:text-text-primary rounded-md hover:bg-surfaceHover transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Overall Match Score */}
        <div className="py-4 flex items-center justify-between border-b border-border">
          <div>
            <div className="text-sm font-medium text-text-secondary">Overall Match Score</div>
            <div className="text-xs text-text-muted">Calculated using transparent normalized criteria</div>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`text-2xl font-bold ${
                job.match_score >= 75
                  ? "text-success"
                  : job.match_score >= 50
                  ? "text-warning"
                  : "text-danger"
              }`}
            >
              {job.match_score}%
            </span>
          </div>
        </div>

        {/* Eligibility Assessment */}
        <div className="py-3 border-b border-border">
          <div className="flex items-center gap-2 mb-1">
            {elig.is_eligible ? (
              <CheckCircle2 className="w-4 h-4 text-success" />
            ) : (
              <XCircle className="w-4 h-4 text-danger" />
            )}
            <span className="text-sm font-semibold text-text-primary">
              {elig.is_eligible ? "Eligible Candidate" : "Flagged: Potentially Ineligible"}
            </span>
          </div>
          {elig.reasons && elig.reasons.length > 0 && (
            <ul className="mt-2 space-y-1">
              {elig.reasons.map((r, i) => (
                <li key={i} className="text-xs text-danger/90 flex items-start gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Detailed Breakdown Categories */}
        <div className="py-4 space-y-3.5">
          <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider">
            Weighted Criteria Breakdown
          </h4>

          {/* Skills Match */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-text-secondary">
                Skills Match ({bd.skills_weight || 40}%)
              </span>
              <span className="font-semibold text-text-primary">{bd.skills_score || 0}%</span>
            </div>
            <div className="w-full bg-surfaceHover h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-primary h-full rounded-full transition-all duration-300"
                style={{ width: `${bd.skills_score || 0}%` }}
              />
            </div>
            {bd.matched_skills && bd.matched_skills.length > 0 && (
              <div className="flex flex-wrap gap-1 pt-1">
                {bd.matched_skills.map((s, idx) => (
                  <span
                    key={idx}
                    className="px-1.5 py-0.5 rounded text-[10px] bg-success/15 text-success"
                  >
                    ✓ {s}
                  </span>
                ))}
                {bd.missing_skills?.map((s, idx) => (
                  <span
                    key={idx}
                    className="px-1.5 py-0.5 rounded text-[10px] bg-danger/10 text-danger/80"
                  >
                    ✕ {s}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Title Relevance */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-text-secondary">
                Job Title Relevance ({bd.title_weight || 25}%)
              </span>
              <span className="font-semibold text-text-primary">{bd.title_score || 0}%</span>
            </div>
            <div className="w-full bg-surfaceHover h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-primary h-full rounded-full"
                style={{ width: `${bd.title_score || 0}%` }}
              />
            </div>
          </div>

          {/* Experience Compatibility */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-text-secondary">
                Experience Compatibility ({bd.experience_weight || 15}%)
              </span>
              <span className="font-semibold text-text-primary">{bd.experience_score || 0}%</span>
            </div>
            <div className="w-full bg-surfaceHover h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-primary h-full rounded-full"
                style={{ width: `${bd.experience_score || 0}%` }}
              />
            </div>
          </div>

          {/* Location & Work Mode */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-text-secondary">
                Location & Work Mode ({bd.location_weight || 10}%)
              </span>
              <span className="font-semibold text-text-primary">{bd.location_score || 0}%</span>
            </div>
            <div className="w-full bg-surfaceHover h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-primary h-full rounded-full"
                style={{ width: `${bd.location_score || 0}%` }}
              />
            </div>
          </div>

          {/* Employment Type */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-text-secondary">
                Employment Type ({bd.employment_type_weight || 10}%)
              </span>
              <span className="font-semibold text-text-primary">{bd.employment_type_score || 0}%</span>
            </div>
            <div className="w-full bg-surfaceHover h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-primary h-full rounded-full"
                style={{ width: `${bd.employment_type_score || 0}%` }}
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-border flex justify-end">
          <button onClick={onClose} className="fluent-button fluent-button-secondary text-xs">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
