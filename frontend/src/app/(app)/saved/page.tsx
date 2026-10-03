"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { JobCard } from "@/components/jobs/job-card";
import type { Job } from "@/types";

type SavedRow = {
  id: string;
  job_id: string;
  notes: string | null;
  job: Job | null;
};

export default function SavedPage() {
  const saved = useQuery({
    queryKey: ["saved"],
    queryFn: () => api<SavedRow[]>("/saved-jobs"),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Saved Jobs</h1>
        <p className="mt-1 text-sm text-ink-muted">Roles you bookmarked for later</p>
      </div>
      <div className="space-y-3">
        {(saved.data || [])
          .filter((r) => r.job)
          .map((r, i) => (
            <JobCard key={r.id} job={r.job!} index={i} />
          ))}
        {!saved.isLoading && !saved.data?.length && (
          <div className="glass-panel p-8 text-center text-sm text-ink-muted">
            No saved jobs yet.
          </div>
        )}
      </div>
    </div>
  );
}
