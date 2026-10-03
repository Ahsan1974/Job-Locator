import type { PaginatedJobs } from "@/types";

/** Reliable next-page detection for infinite job lists. */
export function getJobsNextPageParam(last: PaginatedJobs): number | undefined {
  if (!last.items?.length) return undefined;
  const nextPage = last.page + 1;
  if (nextPage <= last.pages) return nextPage;
  if (last.items.length >= last.page_size && last.page * last.page_size < last.total) {
    return nextPage;
  }
  return undefined;
}

export function dedupeJobs<T extends { id: string }>(jobs: T[]): T[] {
  const seen = new Set<string>();
  return jobs.filter((job) => {
    if (seen.has(job.id)) return false;
    seen.add(job.id);
    return true;
  });
}
