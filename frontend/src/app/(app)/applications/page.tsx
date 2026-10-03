"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { invalidateTrackingQueries } from "@/lib/tracking";
import type { Application, ApplicationStatus } from "@/types";
import {
  Send, Trash2, ExternalLink, StickyNote, Building2, MapPin,
} from "lucide-react";
import { motion } from "framer-motion";
import { formatRelativeDate, formatSalary } from "@/lib/utils";
import Link from "next/link";

const STATUSES: { value: ApplicationStatus; label: string; color: string }[] = [
  { value: "saved", label: "Saved", color: "bg-slate-500/15 text-slate-400" },
  { value: "applied", label: "Applied", color: "bg-blue-500/15 text-blue-400" },
  { value: "screening", label: "Screening", color: "bg-yellow-500/15 text-yellow-400" },
  { value: "interview", label: "Interview", color: "bg-purple-500/15 text-purple-400" },
  { value: "offer", label: "Offer", color: "bg-success/15 text-success" },
  { value: "rejected", label: "Rejected", color: "bg-danger/15 text-danger" },
  { value: "withdrawn", label: "Withdrawn", color: "bg-line/60 text-ink-faint" },
];

function getStatusStyle(status: ApplicationStatus) {
  return STATUSES.find((s) => s.value === status) ?? STATUSES[0];
}

function ApplicationCard({ app, index }: { app: Application; index: number }) {
  const qc = useQueryClient();
  const [showNotes, setShowNotes] = useState(false);
  const [notes, setNotes] = useState(app.notes ?? "");
  const [savingNotes, setSavingNotes] = useState(false);

  const update = useMutation({
    mutationFn: (payload: Partial<Application>) =>
      api(`/applications/${app.id}`, { method: "PATCH", body: JSON.stringify(payload) }),
    onSuccess: () => invalidateTrackingQueries(qc),
  });

  const remove = useMutation({
    mutationFn: () => api(`/applications/${app.id}`, { method: "DELETE" }),
    onSuccess: () => invalidateTrackingQueries(qc),
  });

  async function saveNotes() {
    setSavingNotes(true);
    try {
      await update.mutateAsync({ notes });
    } finally {
      setSavingNotes(false);
      setShowNotes(false);
    }
  }

  const style = getStatusStyle(app.status);
  const job = app.job;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className="glass-panel p-5"
    >
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent">
          <Building2 className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div>
              {job ? (
                <Link
                  href={`/jobs/${app.job_id}`}
                  className="font-semibold text-sm hover:text-accent transition"
                >
                  {job.title}
                </Link>
              ) : (
                <p className="font-semibold text-sm">Job #{app.job_id.slice(0, 8)}</p>
              )}
              {job?.company && (
                <p className="text-xs text-ink-muted mt-0.5">{job.company.name}</p>
              )}
              {job && (job.city || job.country) && (
                <p className="flex items-center gap-1 text-[11px] text-ink-faint mt-1">
                  <MapPin className="h-3 w-3" />
                  {[job.city, job.country].filter(Boolean).join(", ")}
                  {job.work_mode && ` · ${job.work_mode}`}
                </p>
              )}
            </div>
            <div className="flex items-center gap-2 shrink-0 flex-wrap">
              {/* Status selector */}
              <div className="relative">
                <select
                  value={app.status}
                  onChange={(e) => update.mutate({ status: e.target.value as ApplicationStatus })}
                  className={`appearance-none rounded-xl px-3 py-1.5 text-xs font-semibold cursor-pointer border-0 outline-none ${style.color} bg-transparent`}
                >
                  {STATUSES.map((s) => (
                    <option key={s.value} value={s.value}>{s.label}</option>
                  ))}
                </select>
              </div>
              <button
                type="button"
                onClick={() => setShowNotes((v) => !v)}
                className="btn-ghost !px-2 !py-1.5 text-xs"
                title="Notes"
              >
                <StickyNote className="h-3.5 w-3.5" />
              </button>
              {job?.apply_url && (
                <a
                  href={job.apply_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-ghost !px-2 !py-1.5 text-xs"
                  title="Open application"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              )}
              <button
                type="button"
                onClick={() => { if (confirm("Remove this application?")) remove.mutate(); }}
                disabled={remove.isPending}
                className="btn-ghost !px-2 !py-1.5 text-danger hover:bg-danger/10"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-ink-faint">
            {job && (job.salary_min != null || job.salary_max != null) && (
              <span>{formatSalary(job.salary_min, job.salary_max, job.salary_currency)}</span>
            )}
            {app.applied_at && <span>Applied {formatRelativeDate(app.applied_at)}</span>}
            <span>Tracked {formatRelativeDate(app.created_at)}</span>
          </div>
        </div>
      </div>

      {/* Notes section */}
      {showNotes && (
        <div className="mt-4 border-t border-line/60 pt-4">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add notes about this application…"
            className="input-field h-24 resize-none text-xs"
          />
          <div className="mt-2 flex gap-2">
            <button
              type="button"
              onClick={saveNotes}
              disabled={savingNotes}
              className="btn-primary !px-3 !py-1.5 text-xs"
            >
              Save Notes
            </button>
            <button
              type="button"
              onClick={() => { setShowNotes(false); setNotes(app.notes ?? ""); }}
              className="btn-ghost !px-3 !py-1.5 text-xs"
            >
              Cancel
            </button>
          </div>
          {app.notes && !showNotes && (
            <p className="mt-2 text-xs text-ink-muted line-clamp-2">{app.notes}</p>
          )}
        </div>
      )}
    </motion.div>
  );
}

export default function ApplicationsPage() {
  const [activeStatus, setActiveStatus] = useState<ApplicationStatus | "all">("all");

  const { data: applications, isLoading } = useQuery<Application[]>({
    queryKey: ["applications"],
    queryFn: () => api<Application[]>("/applications"),
  });

  const filtered = activeStatus === "all"
    ? applications
    : applications?.filter((a) => a.status === activeStatus);

  const counts = STATUSES.reduce((acc, s) => {
    acc[s.value] = applications?.filter((a) => a.status === s.value).length ?? 0;
    return acc;
  }, {} as Record<ApplicationStatus, number>);

  return (
    <div className="mx-auto max-w-4xl space-y-6 animate-fade-up">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Applications</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Track your job applications from saved to offer.
        </p>
      </div>

      {/* Status tabs */}
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setActiveStatus("all")}
          className={`rounded-xl px-3 py-1.5 text-xs font-medium transition ${
            activeStatus === "all"
              ? "bg-accent text-accent-foreground"
              : "btn-ghost !px-3 !py-1.5"
          }`}
        >
          All ({applications?.length ?? 0})
        </button>
        {STATUSES.map((s) => (
          <button
            key={s.value}
            type="button"
            onClick={() => setActiveStatus(s.value)}
            className={`rounded-xl px-3 py-1.5 text-xs font-medium transition ${
              activeStatus === s.value
                ? "bg-accent text-accent-foreground"
                : "btn-ghost !px-3 !py-1.5"
            }`}
          >
            {s.label}
            {counts[s.value] > 0 && (
              <span className={`ml-1.5 rounded-md px-1.5 py-0.5 text-[10px] ${
                activeStatus === s.value ? "bg-accent-foreground/20" : s.color
              }`}>
                {counts[s.value]}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Application list */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => <div key={i} className="skeleton h-28 w-full" />)}
        </div>
      ) : !filtered?.length ? (
        <div className="glass-panel p-12 text-center">
          <Send className="mx-auto mb-3 h-10 w-10 text-ink-faint" />
          <p className="text-sm font-medium">
            {activeStatus === "all" ? "No applications yet" : `No ${activeStatus} applications`}
          </p>
          <p className="mt-1 text-xs text-ink-faint">
            {activeStatus === "all"
              ? "Apply to a job from the job detail page to track it here."
              : "Change the status filter to see other applications."}
          </p>
          {activeStatus === "all" && (
            <Link href="/jobs" className="btn-primary mt-6 inline-flex">Browse Jobs</Link>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((app, i) => (
            <ApplicationCard key={app.id} app={app} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}
