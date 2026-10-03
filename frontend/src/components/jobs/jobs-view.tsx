"use client";

import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { api } from "@/lib/api";
import { dedupeJobs, getJobsNextPageParam } from "@/lib/jobs-query";
import type { PaginatedJobs } from "@/types";
import { JobCard } from "@/components/jobs/job-card";

const FILTERS = {
  work_mode: ["", "remote", "hybrid", "onsite"],
  experience_level: ["", "entry", "junior", "mid", "senior", "lead", "principal"],
  posted_within: ["", "today", "week", "month"],
};
const ROLE_PRESETS = ["Java", "Python", "AI", "QA", "Project Management"];

type CountryOption = { country: string; count: number };

type JobsViewProps = {
  title?: string;
  subtitle?: string;
  /** Lock to jobs first added to the database today (UTC). */
  addedToday?: boolean;
  hidePostedFilter?: boolean;
  /** Lock employment type, e.g. freelance. */
  employmentType?: string;
  /** Lock the country filter, e.g. Pakistan. */
  lockedCountry?: string;
};

function buildQueryParams(filters: {
  q: string;
  workMode: string;
  visa: boolean;
  experience: string;
  posted: string;
  country: string;
  addedToday?: boolean;
  employmentType?: string;
}): URLSearchParams {
  const p = new URLSearchParams();
  if (filters.q) p.set("q", filters.q);
  if (filters.workMode) p.set("work_mode", filters.workMode);
  if (filters.visa) p.set("visa_sponsorship", "true");
  if (filters.experience) p.set("experience_level", filters.experience);
  if (filters.posted) p.set("posted_within", filters.posted);
  if (filters.country && filters.country !== "All countries") p.set("country", filters.country);
  if (filters.addedToday) p.set("added_today", "true");
  if (filters.employmentType) p.set("employment_type", filters.employmentType);
  return p;
}

function activeFilterLabels(filters: {
  q: string;
  workMode: string;
  visa: boolean;
  experience: string;
  posted: string;
  country: string;
  addedToday?: boolean;
}): string[] {
  const labels: string[] = [];
  if (filters.addedToday) labels.push("Added today");
  if (filters.country) labels.push(filters.country);
  if (filters.workMode) labels.push(filters.workMode);
  if (filters.visa) labels.push("Visa sponsorship");
  if (filters.experience) labels.push(filters.experience);
  if (filters.posted) {
    labels.push(
      filters.posted === "today" ? "Posted today" : filters.posted === "week" ? "Past week" : "Past month",
    );
  }
  if (filters.q) labels.push(`"${filters.q}"`);
  return labels;
}

export function JobsView({
  title = "All Jobs",
  subtitle,
  addedToday = false,
  hidePostedFilter = false,
  employmentType,
  lockedCountry,
}: JobsViewProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const skipUrlSync = useRef(true);

  const [q, setQ] = useState(searchParams.get("q") || "");
  const [workMode, setWorkMode] = useState(searchParams.get("work_mode") || "");
  const [visa, setVisa] = useState(searchParams.get("visa_sponsorship") === "true");
  const [experience, setExperience] = useState(searchParams.get("experience_level") || "");
  const [posted, setPosted] = useState(searchParams.get("posted_within") || "");
  const [country, setCountry] = useState(lockedCountry || searchParams.get("country") || "");

  const { data: countryData } = useQuery({
    queryKey: ["job-countries"],
    queryFn: () => api<{ countries: CountryOption[] }>("/jobs/countries"),
    staleTime: 120_000,
  });

  const { data: sourcesData } = useQuery({
    queryKey: ["job-sources"],
    queryFn: () =>
      api<{ active_now: number; needs_api_key: number; total_catalogued: number }>("/jobs/sources"),
    staleTime: 300_000,
  });

  const filterState = useMemo(
    () => ({ q, workMode, visa, experience, posted, country: lockedCountry || country, addedToday, employmentType }),
    [q, workMode, visa, experience, posted, country, addedToday, employmentType, lockedCountry],
  );

  const queryString = useMemo(() => {
    const p = buildQueryParams(filterState);
    p.set("page_size", "20");
    p.set("sort_by", "created_at");
    p.set("sort_order", addedToday ? "desc" : "desc");
    if (!addedToday) {
      p.set("sort_by", "posted_at");
    }
    return p;
  }, [filterState, addedToday]);

  useEffect(() => {
    if (addedToday || employmentType || lockedCountry || skipUrlSync.current) {
      if (!addedToday && !employmentType && !lockedCountry) skipUrlSync.current = false;
      return;
    }
    const p = buildQueryParams(filterState);
    const qs = p.toString();
    const target = qs ? `/jobs?${qs}` : "/jobs";
    const current = searchParams.toString();
    if (current !== qs) {
      router.replace(target, { scroll: false });
    }
  }, [filterState, router, searchParams, addedToday, employmentType, lockedCountry]);

  const jobs = useInfiniteQuery({
    queryKey: ["jobs", queryString.toString()],
    queryFn: ({ pageParam = 1 }) => {
      const p = new URLSearchParams(queryString);
      p.set("page", String(pageParam));
      return api<PaginatedJobs>(`/jobs?${p.toString()}`);
    },
    getNextPageParam: getJobsNextPageParam,
    initialPageParam: 1,
  });

  const items = useMemo(
    () => dedupeJobs(jobs.data?.pages.flatMap((p) => p.items) ?? []),
    [jobs.data],
  );
  const total = jobs.data?.pages[0]?.total ?? 0;
  const countries = (countryData?.countries ?? []).filter(
    (c) => c.country !== "India" && !c.country.toLowerCase().includes("india"),
  );
  const activeFilters = activeFilterLabels(filterState);
  const hasFilters = activeFilters.length > 0 && !addedToday;
  const hasMore = items.length < total;

  function clearFilters() {
    setQ("");
    setWorkMode("");
    setVisa(false);
    setExperience("");
    setPosted("");
    setCountry("");
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
        <p className="eyebrow">Opportunity finder</p>
        <h1 className="page-title mt-1">{title}</h1>
        <p className="mt-1 text-sm text-ink-muted">
          {subtitle ?? `${total} roles · Java first, plus Python, AI, QA, and project management`}
          {!subtitle && hasFilters && (
            <span className="text-ink-faint"> · filtered by {activeFilters.join(", ")}</span>
          )}
        </p>
        {sourcesData && !addedToday && (
          <p className="mt-1 text-xs text-ink-faint">
            {sourcesData.active_now} live sources · Java is the focus · duplicates hidden
          </p>
        )}
        {addedToday && (
          <p className="mt-1 text-xs text-ink-faint">
            Fresh listings added since midnight UTC. Tomorrow this list resets as new jobs arrive.
          </p>
        )}
        </div>
        {!jobs.isLoading && (
          <div className="text-sm text-ink-muted">
            <span className="font-display text-xl font-semibold text-ink">{total}</span> matches
          </div>
        )}
      </div>

      <section className="glass-panel space-y-4 p-4 sm:p-5" aria-label="Job filters">
        {!addedToday && !employmentType && (
          <div className="flex gap-2 overflow-x-auto pb-1" aria-label="Role presets">
            {ROLE_PRESETS.map((role) => (
              <button
                key={role}
                type="button"
                onClick={() => setQ(q === role ? "" : role)}
                className={`min-h-10 shrink-0 rounded-xl border px-3 py-2 text-sm font-medium transition ${
                  q === role
                    ? "border-accent bg-accent text-accent-foreground shadow-sm"
                    : "border-line bg-canvas-elevated text-ink-muted hover:border-accent/40 hover:text-ink"
                }`}
              >
                {role}
              </button>
            ))}
          </div>
        )}
        <div className="relative">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-faint" />
          <input
            className="input-field min-h-14 pl-12 pr-4 text-base shadow-sm"
            placeholder="Search by role, skill, or company"
            aria-label="Search jobs"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="h-4 w-4 text-accent" />
          <h2 className="text-sm font-semibold">Refine results</h2>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <label className="space-y-1.5 text-xs font-medium text-ink-muted">
            Country
          <select className="input-field" value={country} onChange={(e) => setCountry(e.target.value)}>
            <option value="">All countries</option>
            {countries
              .filter((c) => c.country !== "All countries")
              .map((c) => (
                <option key={c.country} value={c.country}>
                  {c.country}
                  {c.count > 0 ? ` (${c.count})` : ""}
                </option>
              ))}
          </select>
          </label>
          <label className="space-y-1.5 text-xs font-medium text-ink-muted">
            Work mode
          <select className="input-field" value={workMode} onChange={(e) => setWorkMode(e.target.value)}>
            {FILTERS.work_mode.map((v) => (
              <option key={v || "any"} value={v}>
                {v ? v[0].toUpperCase() + v.slice(1) : "Work mode"}
              </option>
            ))}
          </select>
          </label>
          <label className="space-y-1.5 text-xs font-medium text-ink-muted">
            Experience
          <select
            className="input-field"
            value={experience}
            onChange={(e) => setExperience(e.target.value)}
          >
            {FILTERS.experience_level.map((v) => (
              <option key={v || "any"} value={v}>
                {v ? v[0].toUpperCase() + v.slice(1) : "Experience"}
              </option>
            ))}
          </select>
          </label>
          {!hidePostedFilter && (
            <label className="space-y-1.5 text-xs font-medium text-ink-muted">
              Date posted
            <select className="input-field" value={posted} onChange={(e) => setPosted(e.target.value)}>
              {FILTERS.posted_within.map((v) => (
                <option key={v || "any"} value={v}>
                  {v === "today" ? "Posted today" : v === "week" ? "Past week" : v === "month" ? "Past month" : "Posted"}
                </option>
              ))}
            </select>
            </label>
          )}
          <label className="flex min-h-11 cursor-pointer items-center gap-3 rounded-xl border border-line px-3 text-sm text-ink-muted md:col-span-2 xl:col-span-4">
            <input className="h-4 w-4 accent-accent" type="checkbox" checked={visa} onChange={(e) => setVisa(e.target.checked)} />
            Visa sponsorship only
          </label>
        </div>

        {hasFilters && (
          <div className="flex flex-wrap items-center gap-2 border-t border-line/50 pt-3">
            {activeFilters.map((label) => (
              <span key={label} className="rounded-lg bg-accent/10 px-2.5 py-1 text-xs text-accent">
                {label}
              </span>
            ))}
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
      </section>

      <div className="space-y-3">
        {jobs.isLoading &&
          [1, 2, 3, 4].map((i) => <div key={i} className="skeleton h-36 w-full" />)}
        {items.map((job, i) => (
          <JobCard key={job.id} job={job} index={i} />
        ))}
        {jobs.isError && items.length === 0 ? (
          <div className="glass-panel border-danger/30 p-8 text-center">
            <p className="font-semibold text-ink">We couldn’t load jobs right now</p>
            <p className="mt-1 text-sm text-ink-muted">Check your connection, then try again.</p>
            <button type="button" className="btn-primary mt-4" onClick={() => jobs.refetch()}>Try again</button>
          </div>
        ) : !jobs.isLoading && items.length === 0 && (
          <div className="glass-panel p-10 text-center text-sm text-ink-muted">
            {addedToday
              ? "No new jobs added today yet. Click Refresh in the top bar to pull the latest listings."
              : employmentType === "freelance"
                ? "No freelance software gigs yet. Click Refresh in the top bar, then open Freelance Work again."
                : "No matching roles. Try clearing filters or click Refresh in the top bar."}
          </div>
        )}
      </div>

      {(hasMore || jobs.hasNextPage) && (
        <div className="flex flex-col items-center gap-2">
          <button
            type="button"
            className="btn-primary"
            disabled={jobs.isFetchingNextPage}
            onClick={() => jobs.fetchNextPage()}
          >
            {jobs.isFetchingNextPage ? "Loading…" : `Load more (${items.length} of ${total})`}
          </button>
          {jobs.isError && (
            <p className="text-xs text-danger">Failed to load more. Try again.</p>
          )}
        </div>
      )}
    </div>
  );
}
