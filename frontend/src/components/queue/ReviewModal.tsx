import React, { useState } from "react";
import { X, Check, Copy, AlertTriangle, ExternalLink } from "lucide-react";
import { JobApplication } from "../../types";
import { useAppMutations } from "../../api/hooks";

interface ReviewModalProps {
  app: JobApplication | null;
  onClose: () => void;
}

export const ReviewModal: React.FC<ReviewModalProps> = ({ app, onClose }) => {
  const { approveApplication, skipApplication } = useAppMutations();
  const [copied, setCopied] = useState(false);

  if (!app) return null;

  const prep = app.prepared_data || {};
  const job = app.job;

  const handleCopy = () => {
    const text = `Position: ${job?.title} at ${job?.company}\nApplicant: ${prep.full_name}\nEmail: ${prep.email}\nPhone: ${prep.phone}\n\nCover Letter:\n${app.cover_letter}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleApprove = async () => {
    await approveApplication.mutateAsync(app.id);
    onClose();
  };

  const handleSkip = async () => {
    await skipApplication.mutateAsync(app.id);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
      <div className="fluent-card w-full max-w-2xl bg-surface border-border p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between pb-4 border-b border-border">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-text-primary">
                Review Application: {job?.title}
              </h3>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-primary/15 text-primary">
                {app.status}
              </span>
            </div>
            <p className="text-xs text-text-muted mt-0.5">{job?.company} • Match Score: {job?.match_score}%</p>
          </div>
          <button onClick={onClose} className="p-1 text-text-muted hover:text-text-primary">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="py-4 space-y-4">
          {/* Truthful Candidate Profile Summary */}
          <div className="p-3.5 rounded-lg bg-surfaceHover/60 border border-border space-y-2">
            <div className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
              Prepared Applicant Information (Verified Profile)
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-text-muted block">Full Name:</span>
                <span className="font-medium text-text-primary">{prep.full_name || "—"}</span>
              </div>
              <div>
                <span className="text-text-muted block">Email:</span>
                <span className="font-medium text-text-primary">{prep.email || "—"}</span>
              </div>
              <div>
                <span className="text-text-muted block">Phone:</span>
                <span className="font-medium text-text-primary">{prep.phone || "—"}</span>
              </div>
              <div>
                <span className="text-text-muted block">Selected Resume:</span>
                <span className="font-medium text-text-primary">{prep.resume_label || "Primary Resume"}</span>
              </div>
            </div>
          </div>

          {/* Generated Cover Letter */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
                Tailored Truthful Cover Letter
              </label>
              <button
                onClick={handleCopy}
                className="text-xs text-primary hover:underline flex items-center gap-1"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? "Copied" : "Copy to Clipboard"}</span>
              </button>
            </div>
            <textarea
              readOnly
              rows={8}
              value={app.cover_letter}
              className="fluent-input w-full font-mono text-xs leading-relaxed bg-surfaceHover/30 select-all"
            />
          </div>

          {/* Unanswered Questions Flag */}
          {app.unanswered_questions && app.unanswered_questions.length > 0 && (
            <div className="p-3 rounded-lg bg-warning/10 border border-warning/30 flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-warning shrink-0 mt-0.5" />
              <div className="text-xs">
                <span className="font-semibold text-text-primary block">
                  Questions Flagged for User Review
                </span>
                <p className="text-text-secondary mt-0.5">
                  Platform form includes custom questions not found in your profile. Review before submission.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="pt-4 border-t border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            {job?.original_url && (
              <a
                href={job.original_url}
                target="_blank"
                rel="noreferrer"
                className="fluent-button fluent-button-secondary text-xs"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>Open Job Posting</span>
              </a>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleSkip}
              disabled={skipApplication.isPending}
              className="fluent-button fluent-button-secondary text-xs text-danger hover:border-danger/40"
            >
              Skip
            </button>
            <button
              onClick={handleApprove}
              disabled={approveApplication.isPending}
              className="fluent-button fluent-button-primary text-xs"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Approve & Ready to Submit</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
