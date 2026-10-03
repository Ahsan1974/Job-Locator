"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ExternalLink, Bookmark, MapPin, Stamp, Building2,
  Crosshair, Wand2, Mail, Route, GitCompare, Send, Download,
  TrendingUp, CheckCircle, XCircle, AlertCircle,
  PackageCheck,
} from "lucide-react";
import { api, apiBlob } from "@/lib/api";
import { invalidateTrackingQueries } from "@/lib/tracking";
import type { Job, MatchScore, Application } from "@/types";
import { formatRelativeDate, formatSalary } from "@/lib/utils";

function MatchBadge({ score }: { score: number }) {
  const color = score >= 75 ? "text-success" : score >= 50 ? "text-warning" : "text-danger";
  const bg = score >= 75 ? "bg-success/15" : score >= 50 ? "bg-warning/15" : "bg-danger/15";
  return (
    <span className={`inline-flex items-center gap-1 rounded-xl px-3 py-1.5 text-sm font-bold ${bg} ${color}`}>
      <TrendingUp className="h-4 w-4" />
      {score}% match
    </span>
  );
}

function MatchPanel({ jobId }: { jobId: string }) {
  const { data, isLoading, isError } = useQuery<MatchScore>({
    queryKey: ["match", jobId],
    queryFn: () => api<MatchScore>(`/match/job/${jobId}`),
    retry: 1,
  });

  if (isLoading) return <div className="skeleton h-28 w-full" />;
  if (isError || !data) return null;

  const scoreColor = data.overall >= 75 ? "#10b981" : data.overall >= 50 ? "#f59e0b" : "#ef4444";

  return (
    <div className="glass-panel p-5 space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h2 className="font-display text-base font-semibold flex items-center gap-2">
            <Crosshair className="h-4 w-4 text-accent" /> Resume Match
          </h2>
          <p className="text-xs text-ink-faint mt-0.5">Based on your primary resume</p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="font-display text-2xl font-bold"
            style={{ color: scoreColor }}
          >
            {data.overall}
          </span>
          <span className="text-xs text-ink-faint">/100</span>
        </div>
      </div>

      {/* Mini score grid */}
      <div className="grid grid-cols-5 gap-2 text-center">
        {[
          { label: "Skills", value: data.skill_match },
          { label: "Exp", value: data.experience_match },
          { label: "Edu", value: data.education_match },
          { label: "Tech", value: data.technology_match },
          { label: "ATS", value: data.ats_score },
        ].map(({ label, value }) => (
          <div key={label} className="rounded-xl bg-canvas/40 border border-line/60 py-2">
            <p className="font-bold text-sm">{value}</p>
            <p className="text-[10px] text-ink-faint">{label}</p>
          </div>
        ))}
      </div>

      {/* Matching skills */}
      {data.matching_skills.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {data.matching_skills.slice(0, 6).map((s) => (
            <span key={s} className="inline-flex items-center gap-1 rounded-lg bg-success/10 px-2 py-0.5 text-[11px] text-success">
              <CheckCircle className="h-3 w-3" />{s}
            </span>
          ))}
        </div>
      )}

      {/* Missing skills */}
      {data.missing_skills.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {data.missing_skills.slice(0, 4).map((s) => (
            <span key={s} className="inline-flex items-center gap-1 rounded-lg bg-danger/10 px-2 py-0.5 text-[11px] text-danger">
              <XCircle className="h-3 w-3" />{s}
            </span>
          ))}
          {data.missing_skills.length > 4 && (
            <span className="rounded-lg bg-line/40 px-2 py-0.5 text-[11px] text-ink-faint">
              +{data.missing_skills.length - 4} more
            </span>
          )}
        </div>
      )}

      <Link
        href={`/resume/match?job_id=${jobId}`}
        className="btn-ghost w-full justify-center text-xs"
      >
        View Full Analysis →
      </Link>
    </div>
  );
}

export function JobDetailView({ jobId }: { jobId: string }) {
  const router = useRouter();
  const qc = useQueryClient();

  const job = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => api<Job>(`/jobs/${jobId}`),
  });

  const save = useMutation({
    mutationFn: () => api("/saved-jobs", { method: "POST", body: JSON.stringify({ job_id: jobId }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["saved"] }),
  });

  const apply = useMutation({
    mutationFn: () =>
      api<Application>("/applications", {
        method: "POST",
        body: JSON.stringify({ job_id: jobId, status: "applied" }),
      }),
    onSuccess: () => {
      invalidateTrackingQueries(qc);
      router.push("/applications");
    },
  });

  const applicationPack = useMutation({
    mutationFn: () =>
      apiBlob("/ai/application-pack/pdf", {
        method: "POST",
        body: JSON.stringify({ job_id: jobId }),
      }),
    onSuccess: (blob) => {
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "application-pack.pdf";
      anchor.click();
      URL.revokeObjectURL(url);
    },
  });

  if (job.isLoading) {
    return <div className="skeleton h-96 w-full" />;
  }
  if (job.isError || !job.data) {
    return <div className="glass-panel p-8 text-sm text-danger">Job not found.</div>;
  }

  const j = job.data;
  let stack: string[] = [];
  try {
    stack = j.technology_stack ? JSON.parse(j.technology_stack) : [];
  } catch {
    stack = [];
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 pb-24 animate-fade-up md:pb-0">
      {/* Main header card */}
      <div className="glass-panel p-6 md:p-8">
        <div className="flex flex-wrap items-start gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/15 text-accent">
            <Building2 className="h-6 w-6" />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="font-display text-3xl font-semibold tracking-tight">{j.title}</h1>
            {j.company?.slug ? (
              <Link href={`/companies/${j.company.slug}`} className="mt-1 text-ink-muted hover:text-accent">
                {j.company.name}
              </Link>
            ) : (
              <p className="mt-1 text-ink-muted">{j.company?.name}</p>
            )}
            <div className="mt-3 flex flex-wrap gap-2 text-xs text-ink-muted">
              {(j.city || j.country) && (
                <span className="inline-flex items-center gap-1 rounded-lg bg-line/40 px-2 py-1">
                  <MapPin className="h-3 w-3" />
                  {[j.city, j.country].filter(Boolean).join(", ")}
                </span>
              )}
              {j.work_mode && (
                <span className="rounded-lg bg-line/40 px-2 py-1 capitalize">{j.work_mode}</span>
              )}
              {j.employment_type && (
                <span className="rounded-lg bg-line/40 px-2 py-1 capitalize">
                  {j.employment_type.replace("_", " ")}
                </span>
              )}
              {j.visa_sponsorship && (
                <span className="inline-flex items-center gap-1 rounded-lg bg-success/15 px-2 py-1 text-success">
                  <Stamp className="h-3 w-3" /> Visa sponsorship
                </span>
              )}
              {j.match_score != null && <MatchBadge score={j.match_score} />}
            </div>
          </div>

          {/* Action buttons */}
          <div className="grid w-full grid-cols-1 gap-2 sm:flex sm:w-auto sm:flex-wrap">
            <button
              type="button"
              className="btn-primary justify-center"
              onClick={() => applicationPack.mutate()}
              disabled={applicationPack.isPending}
            >
              <PackageCheck className="h-4 w-4" />
              {applicationPack.isPending ? "Building pack…" : "Download Apply Pack"}
            </button>
            <Link
              href={`/resume/optimizer?job_id=${jobId}`}
              className="btn-primary"
            >
              <Wand2 className="h-4 w-4" /> Tailor CV for This Job
            </Link>
            <Link
              href={`/resume/optimizer?job_id=${jobId}`}
              className="btn-ghost"
              title="Opens optimizer with PDF download"
            >
              <Download className="h-4 w-4" /> PDF
            </Link>
            <button
              type="button"
              className="btn-ghost"
              onClick={() => save.mutate()}
              disabled={save.isPending}
            >
              <Bookmark className="h-4 w-4" /> Save
            </button>
            <button
              type="button"
              className="btn-primary"
              onClick={() => {
                apply.mutate();
                if (j.apply_url) {
                  window.open(j.apply_url, "_blank", "noopener,noreferrer");
                }
              }}
              disabled={apply.isPending}
            >
              {apply.isPending ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-accent-foreground border-t-transparent" />
              ) : (
                <Send className="h-4 w-4" />
              )}
              Apply & Track
            </button>
            {j.apply_url && (
              <a href={j.apply_url} target="_blank" rel="noopener noreferrer" className="btn-ghost">
                Open posting <ExternalLink className="h-4 w-4" />
              </a>
            )}
          </div>
        </div>

        {/* AI action row */}
        <div className="mt-5 flex flex-wrap gap-2 border-t border-line/60 pt-4">
          <Link href={`/resume/match?job_id=${jobId}`} className="btn-ghost !px-3 !py-1.5 text-xs">
            <Crosshair className="h-3.5 w-3.5" /> Match Score
          </Link>
          <Link href={`/cover-letter?job_id=${jobId}`} className="btn-ghost !px-3 !py-1.5 text-xs">
            <Mail className="h-3.5 w-3.5" /> Cover Letter
          </Link>
          <Link href={`/resume/optimizer?job_id=${jobId}`} className="btn-ghost !px-3 !py-1.5 text-xs">
            <Wand2 className="h-3.5 w-3.5" /> Tailor CV
          </Link>
          <Link href={`/skill-gap?job_id=${jobId}`} className="btn-ghost !px-3 !py-1.5 text-xs">
            <Route className="h-3.5 w-3.5" /> Skill Gap
          </Link>
          <Link href={`/interview?job_id=${jobId}`} className="btn-ghost !px-3 !py-1.5 text-xs">
            Interview Prep
          </Link>
          <Link href={`/salary?job_id=${jobId}`} className="btn-ghost !px-3 !py-1.5 text-xs">
            Salary Estimate
          </Link>
          <Link href={`/jobs/${jobId}/compare`} className="btn-ghost !px-3 !py-1.5 text-xs">
            <GitCompare className="h-3.5 w-3.5" /> Live Compare
          </Link>
        </div>

        {/* Info grid */}
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-line/70 bg-canvas/40 p-4">
            <p className="text-xs text-ink-faint">Compensation</p>
            <p className="mt-1 font-medium">
              {formatSalary(j.salary_min, j.salary_max, j.salary_currency)}
            </p>
          </div>
          <div className="rounded-xl border border-line/70 bg-canvas/40 p-4">
            <p className="text-xs text-ink-faint">Posted</p>
            <p className="mt-1 font-medium">{formatRelativeDate(j.posted_at)}</p>
          </div>
          <div className="rounded-xl border border-line/70 bg-canvas/40 p-4">
            <p className="text-xs text-ink-faint">Source</p>
            <p className="mt-1 font-medium capitalize">{j.source}</p>
          </div>
        </div>
      </div>

      {/* Match panel */}
      <MatchPanel jobId={jobId} />

      {stack.length > 0 && (
        <div className="glass-panel p-6">
          <h2 className="font-display text-lg font-semibold">Technology stack</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {stack.map((t) => (
              <span key={t} className="rounded-lg bg-accent/10 px-2.5 py-1 text-xs font-medium text-accent">
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      {j.description && (
        <div className="glass-panel p-6 prose-invert">
          <h2 className="font-display text-lg font-semibold">Description</h2>
          <div
            className="mt-3 text-sm leading-relaxed text-ink-muted [&_ul]:list-disc [&_ul]:pl-5"
            dangerouslySetInnerHTML={{ __html: j.description }}
          />
        </div>
      )}

      {j.requirements && (
        <div className="glass-panel p-6">
          <h2 className="font-display text-lg font-semibold">Requirements</h2>
          <p className="mt-3 whitespace-pre-wrap text-sm text-ink-muted">{j.requirements}</p>
        </div>
      )}

      {j.benefits && (
        <div className="glass-panel p-6">
          <h2 className="font-display text-lg font-semibold">Benefits</h2>
          <p className="mt-3 whitespace-pre-wrap text-sm text-ink-muted">{j.benefits}</p>
        </div>
      )}

      {j.company?.website && (
        <div className="glass-panel p-6 flex items-center justify-between gap-4">
          <div>
            <h2 className="font-display text-lg font-semibold">Company website</h2>
            <p className="text-sm text-ink-muted">{j.company.website}</p>
          </div>
          <a href={j.company.website} target="_blank" rel="noopener noreferrer" className="btn-ghost">
            Visit <ExternalLink className="h-4 w-4" />
          </a>
        </div>
      )}

      {/* Apply error */}
      {apply.isError && (
        <div className="glass-panel p-4 flex items-start gap-3 text-sm text-danger">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <p>{(apply.error as Error).message}</p>
        </div>
      )}
      {applicationPack.isError && (
        <div className="glass-panel p-4 flex items-start gap-3 text-sm text-danger">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <p>{(applicationPack.error as Error).message}</p>
        </div>
      )}
      <div className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-canvas/95 p-3 backdrop-blur-xl md:hidden">
        <div className="mx-auto flex max-w-5xl gap-2">
          <button
            type="button"
            className="btn-primary min-h-12 flex-1 justify-center"
            disabled={apply.isPending}
            onClick={() => {
              apply.mutate();
              if (j.apply_url) window.open(j.apply_url, "_blank", "noopener,noreferrer");
            }}
          >
            <Send className="h-4 w-4" />
            {apply.isPending ? "Tracking…" : "Apply & Track"}
          </button>
          {j.apply_url && (
            <a
              href={j.apply_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-ghost min-h-12 justify-center"
            >
              <ExternalLink className="h-4 w-4" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
