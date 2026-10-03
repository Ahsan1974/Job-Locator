"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { MapPin, Stamp, Globe2, Building2, ExternalLink, EyeOff } from "lucide-react";
import { api } from "@/lib/api";
import { invalidateTrackingQueries } from "@/lib/tracking";
import type { Job } from "@/types";
import { cn, formatRelativeDate, formatSalary } from "@/lib/utils";

export function JobCard({ job, index = 0 }: { job: Job; index?: number }) {
  const qc = useQueryClient();
  const router = useRouter();

  const trackApply = useMutation({
    mutationFn: () =>
      api("/applications", {
        method: "POST",
        body: JSON.stringify({ job_id: job.id, status: "applied" }),
      }),
    onSuccess: () => invalidateTrackingQueries(qc),
  });
  const dismiss = useMutation({
    mutationFn: () =>
      api(`/jobs/${job.id}/dismiss`, {
        method: "POST",
        body: JSON.stringify({ reason: "not_interested" }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  });
  const postedTime = job.posted_at ? new Date(job.posted_at).getTime() : Date.now();
  const isStale = Date.now() - postedTime > 30 * 24 * 60 * 60 * 1000;

  function handleApplyClick() {
    trackApply.mutate();
    if (job.apply_url) {
      window.open(job.apply_url, "_blank", "noopener,noreferrer");
    }
  }

  return (
    <article
      className={cn(
        "glass-panel group animate-fade-up cursor-pointer p-4 transition duration-200 hover:-translate-y-0.5 hover:border-accent/35 hover:shadow-lg hover:shadow-accent/5 sm:p-5",
        isStale && "opacity-70",
      )}
      style={{ animationDelay: `${Math.min(index, 8) * 40}ms` }}
      onClick={(event) => {
        if (!(event.target as HTMLElement).closest("a, button, input, select, textarea")) {
          router.push(`/jobs/${job.id}`);
        }
      }}
    >
      <div className="flex items-start gap-3 sm:gap-4">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-line/70 bg-canvas text-accent sm:h-14 sm:w-14">
          {job.company?.logo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={job.company.logo_url} alt="" className="h-9 w-9 rounded-lg object-contain" />
          ) : (
            <Building2 className="h-5 w-5" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <Link
                href={`/jobs/${job.id}`}
                className="font-display text-lg font-semibold leading-snug tracking-tight transition hover:text-accent"
              >
                {job.title}
              </Link>
              {job.company?.slug ? (
                <Link
                  href={`/companies/${job.company.slug}`}
                className="mt-1 block text-sm font-medium text-ink-muted hover:text-accent"
                >
                  {job.company.name}
                </Link>
              ) : (
                <p className="mt-0.5 text-sm text-ink-muted">
                  {job.company?.name || "Unknown company"}
                </p>
              )}
            </div>
            {job.recommendation_score != null && (
              <div className="rounded-lg bg-accent/10 px-2.5 py-1 text-xs font-semibold text-accent">
                {Number(job.recommendation_score).toFixed(0)}% fit
              </div>
            )}
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2 text-xs text-ink-muted">
            {(job.city || job.country) && (
              <span className="inline-flex items-center gap-1">
                <MapPin className="h-3 w-3" />
                {[job.city, job.country].filter(Boolean).join(", ")}
              </span>
            )}
            {job.work_mode && (
              <span className="inline-flex items-center gap-1 capitalize">
                <Globe2 className="h-3 w-3" />
                {job.work_mode}
              </span>
            )}
            {job.visa_sponsorship && (
              <span className="inline-flex items-center gap-1 rounded-md bg-success/10 px-2 py-1 font-medium text-success">
                <Stamp className="h-3 w-3" />
                Visa
              </span>
            )}
            {job.experience_level && (
              <span className="capitalize">{job.experience_level}</span>
            )}
          </div>

          <div className="mt-4 border-t border-line/60 pt-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="text-sm font-semibold">
              {formatSalary(job.salary_min, job.salary_max, job.salary_currency)}
              {job.salary_estimated && (
                <span className="ml-2 text-xs font-normal text-ink-faint">est.</span>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-2 text-xs text-ink-faint sm:gap-3">
              <span>{formatRelativeDate(job.posted_at)}</span>
              {isStale && <span className="rounded-md bg-warning/10 px-1.5 py-0.5 text-warning">Older listing</span>}
              <span
                className={cn(
                  "rounded-md px-1.5 py-0.5 uppercase tracking-wide",
                  job.source === "linkedin" ? "bg-[#0A66C2]/15 text-[#0A66C2]" : "bg-line/50",
                )}
              >
                {job.source === "linkedin" ? "LinkedIn" : job.source}
              </span>
            </div>
            </div>
            <div className="mt-3 flex items-center gap-2 sm:justify-end">
              {job.apply_url ? (
                <button
                  type="button"
                  onClick={handleApplyClick}
                  disabled={trackApply.isPending}
                  className="inline-flex min-h-11 flex-1 items-center justify-center gap-1.5 rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-accent-foreground shadow-sm transition hover:brightness-110 sm:flex-none"
                  title="Opens apply link and tracks on your dashboard"
                >
                  Apply & Track <ExternalLink className="h-3 w-3" />
                </button>
              ) : (
                <Link href={`/jobs/${job.id}`} className="btn-primary flex-1 sm:flex-none">
                  View
                </Link>
              )}
              <button
                type="button"
                onClick={() => dismiss.mutate()}
                disabled={dismiss.isPending}
                className="inline-flex min-h-11 items-center gap-1.5 rounded-xl px-3 text-sm text-ink-muted transition hover:bg-line/50 hover:text-ink"
                title="Hide this job from your lists"
              >
                <EyeOff className="h-3.5 w-3.5" />
                Not interested
              </button>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}
