"use client";

import { useInfiniteQuery, useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { RefreshCw, X, ExternalLink } from "lucide-react";
import { LinkedInIcon } from "@/components/icons/linkedin-icon";
import { api } from "@/lib/api";
import { dedupeJobs, getJobsNextPageParam } from "@/lib/jobs-query";
import type { PaginatedJobs } from "@/types";
import { JobCard } from "@/components/jobs/job-card";

const FILTERS = {
  work_mode: ["", "remote", "hybrid", "onsite"],
};

type CountryOption = { country: string; count: number };

function buildQueryParams(filters: {
  q: string;
  workMode: string;
  visa: boolean;
  country: string;
}): URLSearchParams {
  const p = new URLSearchParams();
  p.set("source", "linkedin");
  if (filters.q) p.set("q", filters.q);
  if (filters.workMode) p.set("work_mode", filters.workMode);
  if (filters.visa) p.set("visa_sponsorship", "true");
  if (filters.country && filters.country !== "All countries") p.set("country", filters.country);
  return p;
}

export function LinkedInJobsView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const qc = useQueryClient();
  const skipUrlSync = useRef(true);

  const [q, setQ] = useState(searchParams.get("q") || "");
  const [workMode, setWorkMode] = useState(searchParams.get("work_mode") || "");
  const [visa, setVisa] = useState(searchParams.get("visa_sponsorship") === "true");
  const [country, setCountry] = useState(searchParams.get("country") || "");

  const filterState = useMemo(() => ({ q, workMode, visa, country }), [q, workMode, visa, country]);

  const queryString = useMemo(() => {
    const p = buildQueryParams(filterState);
    p.set("page_size", "20");
    return p;
  }, [filterState]);

  useEffect(() => {
    if (skipUrlSync.current) {
      skipUrlSync.current = false;
      return;
    }
    const p = buildQueryParams(filterState);
    const qs = p.toString();
    const target = `/jobs/linkedin?${qs}`;
    if (searchParams.toString() !== qs) {
      router.replace(target, { scroll: false });
    }
  }, [filterState, router, searchParams]);

  const { data: countryData } = useQuery({
    queryKey: ["linkedin-job-countries"],
    queryFn: async () => {
      const res = await api<PaginatedJobs>("/jobs?source=linkedin&page_size=1");
      const countries = await api<{ countries: CountryOption[] }>("/jobs/countries");
      return {
        total: res.total,
        countries: countries.countries.filter(
          (c) => c.country !== "All countries" && c.country !== "India" && c.count > 0,
        ),
      };
    },
    staleTime: 120_000,
  });

  const jobs = useInfiniteQuery({
    queryKey: ["linkedin-jobs", queryString.toString()],
    queryFn: ({ pageParam = 1 }) => {
      const p = new URLSearchParams(queryString);
      p.set("page", String(pageParam));
      return api<PaginatedJobs>(`/jobs?${p.toString()}`);
    },
    getNextPageParam: getJobsNextPageParam,
    initialPageParam: 1,
  });

  const refreshLinkedIn = useMutation({
    mutationFn: () => api<{ status: string; source: string; count: number }>("/jobs/refresh?source=linkedin", { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["linkedin-jobs"] });
      qc.invalidateQueries({ queryKey: ["linkedin-job-countries"] });
      qc.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  const items = useMemo(
    () => dedupeJobs(jobs.data?.pages.flatMap((p) => p.items) ?? []),
    [jobs.data],
  );
  const total = jobs.data?.pages[0]?.total ?? countryData?.total ?? 0;
  const hasMore = items.length < total;
  const countries = countryData?.countries ?? [];
  const hasFilters = !!(country || workMode || visa || q);

  function clearFilters() {
    setQ("");
    setWorkMode("");
    setVisa(false);
    setCountry("");
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#0A66C2]/15 text-[#0A66C2]">
              <LinkedInIcon className="h-5 w-5" />
            </div>
            <div>
              <h1 className="font-display text-3xl font-semibold tracking-tight">LinkedIn Jobs</h1>
              <p className="text-sm text-ink-muted">
                {total} LinkedIn roles · Java, Python, AI, QA, and project management
              </p>
            </div>
          </div>
          <p className="mt-2 text-xs text-ink-faint max-w-2xl">
            Listings are pulled from LinkedIn&apos;s public job search. Each card links to the original LinkedIn posting.
            Use filters below for country, remote/onsite, or visa sponsorship.
          </p>
        </div>
        <button
          type="button"
          onClick={() => refreshLinkedIn.mutate()}
          disabled={refreshLinkedIn.isPending}
          className="btn-primary shrink-0"
        >
          <RefreshCw className={`h-4 w-4 ${refreshLinkedIn.isPending ? "animate-spin" : ""}`} />
          {refreshLinkedIn.isPending ? "Fetching…" : "Refresh LinkedIn"}
        </button>
      </div>

      <div className="glass-panel space-y-3 p-4">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <input
            className="input-field xl:col-span-2"
            placeholder="Search Java roles…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <select className="input-field" value={country} onChange={(e) => setCountry(e.target.value)}>
            <option value="">All countries</option>
            {countries.map((c) => (
              <option key={c.country} value={c.country}>
                {c.country} ({c.count})
              </option>
            ))}
          </select>
          <select className="input-field" value={workMode} onChange={(e) => setWorkMode(e.target.value)}>
            {FILTERS.work_mode.map((v) => (
              <option key={v || "any"} value={v}>
                {v ? v[0].toUpperCase() + v.slice(1) : "All work modes"}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-sm text-ink-muted xl:col-span-4">
            <input type="checkbox" checked={visa} onChange={(e) => setVisa(e.target.checked)} />
            Visa sponsorship only
          </label>
        </div>
        {hasFilters && (
          <div className="flex items-center gap-2 border-t border-line/50 pt-3">
            <button
              type="button"
              onClick={clearFilters}
              className="ml-auto flex items-center gap-1 text-xs text-ink-muted hover:text-ink transition"
            >
              <X className="h-3 w-3" />
              Clear filters
            </button>
          </div>
        )}
      </div>

      <div className="space-y-3">
        {jobs.isLoading && [1, 2, 3, 4].map((i) => <div key={i} className="skeleton h-36 w-full" />)}
        {items.map((job, i) => (
          <JobCard key={job.id} job={job} index={i} />
        ))}
        {!jobs.isLoading && items.length === 0 && (
          <div className="glass-panel p-10 text-center text-sm text-ink-muted space-y-3">
            <p>No LinkedIn Java jobs in the database yet.</p>
            <button
              type="button"
              onClick={() => refreshLinkedIn.mutate()}
              disabled={refreshLinkedIn.isPending}
              className="btn-primary mx-auto"
            >
              <RefreshCw className={`h-4 w-4 ${refreshLinkedIn.isPending ? "animate-spin" : ""}`} />
              Fetch LinkedIn jobs now
            </button>
            <p className="text-xs text-ink-faint">
              Scraping may take 1–2 minutes. Ensure <code className="text-accent">ENABLE_LINKEDIN_SCRAPING=true</code> in .env
            </p>
            <a
              href="https://www.linkedin.com/jobs/search/?keywords=java%20developer"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-accent hover:underline"
            >
              Browse on LinkedIn <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        )}
      </div>

      {(hasMore || jobs.hasNextPage) && (
        <div className="flex justify-center">
          <button
            type="button"
            className="btn-primary"
            disabled={jobs.isFetchingNextPage}
            onClick={() => jobs.fetchNextPage()}
          >
            {jobs.isFetchingNextPage ? "Loading…" : `Load more (${items.length} of ${total})`}
          </button>
        </div>
      )}
    </div>
  );
}
