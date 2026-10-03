"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PaginatedJobs } from "@/types";
import { Briefcase } from "lucide-react";

export function JobPicker({
  title = "Select a job",
  description = "Choose a job posting to continue.",
  basePath,
}: {
  title?: string;
  description?: string;
  basePath: string;
}) {
  const jobs = useQuery({
    queryKey: ["job-picker"],
    queryFn: () => api<PaginatedJobs>("/jobs?page_size=12&sort_by=posted_at"),
    staleTime: 60_000,
  });

  const items = jobs.data?.items ?? [];

  return (
    <div className="glass-panel p-8 space-y-5">
      <div className="text-center">
        <Briefcase className="mx-auto mb-3 h-10 w-10 text-ink-faint" />
        <h2 className="font-display text-xl font-semibold">{title}</h2>
        <p className="mt-2 text-sm text-ink-muted">{description}</p>
      </div>

      {jobs.isLoading && <div className="skeleton h-32 w-full" />}

      {!jobs.isLoading && items.length === 0 && (
        <p className="text-center text-sm text-ink-muted">
          No jobs loaded yet.{" "}
          <Link href="/jobs" className="text-accent hover:underline">
            Browse jobs
          </Link>{" "}
          or click Refresh in the top bar.
        </p>
      )}

      <div className="space-y-2">
        {items.map((job) => (
          <Link
            key={job.id}
            href={`${basePath}?job_id=${job.id}`}
            className="flex items-center justify-between gap-3 rounded-xl border border-line/60 bg-canvas/40 px-4 py-3 text-sm transition hover:border-accent/40 hover:bg-accent/5"
          >
            <div className="min-w-0">
              <p className="truncate font-medium">{job.title}</p>
              <p className="truncate text-xs text-ink-muted">
                {job.company?.name}
                {(job.city || job.country) && ` · ${[job.city, job.country].filter(Boolean).join(", ")}`}
              </p>
            </div>
            <span className="shrink-0 text-xs text-accent">Select →</span>
          </Link>
        ))}
      </div>

      <div className="text-center">
        <Link href="/jobs" className="btn-ghost text-xs">
          View all jobs
        </Link>
      </div>
    </div>
  );
}
