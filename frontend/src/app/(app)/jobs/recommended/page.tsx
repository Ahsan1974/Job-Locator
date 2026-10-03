"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PaginatedRecommendations, Job } from "@/types";
import { JobCard } from "@/components/jobs/job-card";
import { Sparkles, RefreshCw, AlertCircle } from "lucide-react";

const PRIORITIES = ["all", "high", "medium", "low"] as const;
type Priority = (typeof PRIORITIES)[number];

const PRIORITY_COLORS: Record<string, string> = {
  high: "bg-success/15 text-success",
  medium: "bg-warning/15 text-warning",
  low: "bg-line/60 text-ink-muted",
};

export default function RecommendedPage() {
  const qc = useQueryClient();
  const [priority, setPriority] = useState<Priority>("all");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError } = useQuery<PaginatedRecommendations>({
    queryKey: ["recommendations", priority, page],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), page_size: "20" });
      if (priority !== "all") params.set("priority", priority);
      return api<PaginatedRecommendations>(`/recommendations?${params}`);
    },
  });

  const recompute = useMutation({
    mutationFn: () => api("/recommendations/recompute", { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["recommendations"] }),
  });

  return (
    <div className="mx-auto max-w-5xl space-y-6 animate-fade-up">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Recommended Jobs</h1>
          <p className="mt-1 text-sm text-ink-muted">
            AI-ranked opportunities based on your primary resume and preferences.
          </p>
        </div>
        <button
          type="button"
          onClick={() => recompute.mutate()}
          disabled={recompute.isPending}
          className="btn-ghost shrink-0"
        >
          <RefreshCw className={`h-4 w-4 ${recompute.isPending ? "animate-spin" : ""}`} />
          Recompute
        </button>
      </div>

      {/* Priority filter */}
      <div className="flex flex-wrap gap-2">
        {PRIORITIES.map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => { setPriority(p); setPage(1); }}
            className={`rounded-xl px-3 py-1.5 text-xs font-medium capitalize transition ${
              priority === p
                ? "bg-accent text-accent-foreground"
                : "btn-ghost !px-3 !py-1.5"
            }`}
          >
            {p === "all" ? "All Priorities" : (
              <span className={`inline-flex items-center gap-1.5 ${priority !== p ? PRIORITY_COLORS[p] : ""}`}>
                {p}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Results */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {[1,2,3,4].map((i) => <div key={i} className="skeleton h-48 w-full" />)}
        </div>
      ) : isError ? (
        <div className="glass-panel p-8 flex items-start gap-3 text-sm text-danger">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Could not load recommendations</p>
            <p className="mt-1 text-xs text-ink-muted">
              Upload a primary resume to generate personalized recommendations.
            </p>
          </div>
        </div>
      ) : !data?.items?.length ? (
        <div className="glass-panel p-12 text-center">
          <Sparkles className="mx-auto mb-3 h-10 w-10 text-ink-faint" />
          <p className="text-sm font-medium">No recommendations yet</p>
          <p className="mt-1 text-xs text-ink-faint">
            Upload a primary resume and click Recompute to generate recommendations.
          </p>
          <button
            type="button"
            onClick={() => recompute.mutate()}
            disabled={recompute.isPending}
            className="btn-primary mt-6"
          >
            {recompute.isPending ? "Computing…" : "Compute Now"}
          </button>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <p className="text-xs text-ink-faint">{data.total} recommendations</p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {data.items.map((job: Job, i: number) => (
              <div key={job.id} className="relative">
                {job.recommendation_priority && (
                  <div className={`absolute -top-2 left-4 z-10 rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${
                    PRIORITY_COLORS[job.recommendation_priority] ?? "bg-line/60 text-ink-faint"
                  }`}>
                    {job.recommendation_priority} match
                  </div>
                )}
                <JobCard job={job} index={i} />
              </div>
            ))}
          </div>

          {/* Pagination */}
          {data.pages > 1 && (
            <div className="flex justify-center gap-2">
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-ghost !px-3 !py-1.5 text-xs"
              >
                Previous
              </button>
              <span className="flex items-center text-xs text-ink-faint">
                {page} / {data.pages}
              </span>
              <button
                type="button"
                onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                disabled={page === data.pages}
                className="btn-ghost !px-3 !py-1.5 text-xs"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
