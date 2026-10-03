"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Briefcase,
  Building2,
  Globe2,
  Stamp,
  DollarSign,
  Map,
  Bookmark,
  Send,
  Sparkles,
  PlusCircle,
  ArrowRight,
  Search,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { ActivityItem, DashboardStats, Job } from "@/types";
import { StatCard } from "@/components/dashboard/stat-card";
import { JobCard } from "@/components/jobs/job-card";
import { formatSalary } from "@/lib/utils";

export function DashboardView() {
  const stats = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => api<DashboardStats>("/dashboard/stats"),
  });
  const latest = useQuery({
    queryKey: ["latest-jobs"],
    queryFn: () => api<Job[]>("/dashboard/latest-jobs?limit=6"),
  });
  const activity = useQuery({
    queryKey: ["activity"],
    queryFn: () => api<ActivityItem[]>("/dashboard/activity"),
  });

  const s = stats.data;

  return (
    <div className="space-y-7">
      <section className="relative overflow-hidden rounded-3xl bg-[#211a43] px-5 py-6 text-white shadow-glass sm:px-7 sm:py-8">
        <div className="absolute -right-16 -top-24 h-72 w-72 rounded-full bg-accent/40 blur-3xl" />
        <div className="absolute bottom-0 right-1/4 h-32 w-32 rounded-full bg-success/15 blur-3xl" />
        <div className="relative grid gap-6 lg:grid-cols-[1fr_auto] lg:items-end">
          <div className="max-w-2xl animate-fade-up">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-200">Your daily briefing</p>
            <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight sm:text-4xl">
              Welcome back. Your next role may be in today’s shortlist.
            </h1>
            <p className="mt-3 max-w-xl text-sm leading-6 text-violet-100/80">
              Java-focused opportunities, with Python, AI, QA, project management, and freelance work in one place.
            </p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Link href="/jobs/today" className="btn-primary bg-white text-[#211a43] shadow-none hover:bg-violet-50">
              <PlusCircle className="h-4 w-4" />
              {s?.jobs_added_today ?? "—"} new today
            </Link>
            <Link href="/jobs" className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-white/20 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-white/10">
              <Search className="h-4 w-4" />
              Explore jobs
            </Link>
          </div>
        </div>
      </section>

      <section aria-labelledby="snapshot-title">
        <div className="mb-3 flex items-end justify-between gap-4">
          <div>
            <p className="eyebrow">At a glance</p>
            <h2 id="snapshot-title" className="mt-1 font-display text-xl font-semibold">Search snapshot</h2>
          </div>
          <Link href="/analytics" className="hidden items-center gap-1 text-sm font-medium text-accent hover:underline sm:flex">
            View analytics <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
        <div className="grid grid-cols-2 gap-3 xl:grid-cols-5">
          <StatCard index={0} label="Total Jobs" value={s?.total_jobs ?? "—"} icon={Briefcase} accent />
          <StatCard index={1} label="Remote" value={s?.remote_jobs ?? "—"} icon={Globe2} />
          <StatCard index={2} label="Visa Sponsorship" value={s?.visa_sponsorship_jobs ?? "—"} icon={Stamp} />
        <StatCard
          index={3}
          label="Avg Salary"
          value={s?.average_salary != null ? formatSalary(s.average_salary, s.average_salary) : "—"}
          icon={DollarSign}
        />
          <StatCard index={4} label="Recommended" value={s?.recommended_jobs ?? "—"} icon={Sparkles} />
        </div>
        <div className="mt-3 grid grid-cols-2 overflow-hidden rounded-2xl border border-line/80 bg-canvas-elevated sm:grid-cols-5">
          {[
            { label: "Countries", value: s?.countries_count ?? "—", icon: Map },
            { label: "Companies", value: s?.companies_hiring ?? "—", icon: Building2 },
            { label: "Saved", value: s?.saved_jobs ?? "—", icon: Bookmark },
            { label: "Applications", value: s?.applications ?? "—", icon: Send },
            { label: "Added today", value: s?.jobs_added_today ?? "—", icon: PlusCircle },
          ].map(({ label, value, icon: Icon }) => (
            <div key={label} className="flex items-center gap-3 border-b border-r border-line/70 px-4 py-3 even:border-r-0 last:col-span-2 last:border-b-0 sm:border-b-0 sm:border-r sm:even:border-r sm:last:col-span-1 sm:last:border-r-0">
              <Icon className="h-4 w-4 text-accent" />
              <div>
                <p className="text-xs text-ink-muted">{label}</p>
                <p className="font-display text-lg font-semibold">{value}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-3">
        <section className="space-y-3 xl:col-span-2">
          <div className="flex items-end justify-between">
            <div>
              <p className="eyebrow">Fresh opportunities</p>
              <h2 className="mt-1 font-display text-xl font-semibold">Latest roles</h2>
            </div>
            <Link href="/jobs" className="flex items-center gap-1 text-sm font-medium text-accent hover:underline">
              View all <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          {latest.isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="skeleton h-32 w-full" />
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {(latest.data || []).map((job, i) => (
                <JobCard key={job.id} job={job} index={i} />
              ))}
              {!latest.data?.length && (
                <div className="glass-panel p-8 text-center text-sm text-ink-muted">
                  No jobs yet. Click <strong>Refresh</strong> in the top bar to pull from live sources,
                  or run the seed script.
                </div>
              )}
            </div>
          )}
        </section>

        <section className="space-y-3">
          <div>
            <p className="eyebrow">Your progress</p>
            <h2 className="mt-1 font-display text-xl font-semibold">Recent activity</h2>
          </div>
          <div className="glass-panel divide-y divide-line/60 p-2">
            {(activity.data || []).length === 0 && (
              <p className="p-4 text-sm text-ink-muted">No activity yet — save or apply to a role to begin.</p>
            )}
            {(activity.data || []).map((item) => (
              <div key={item.id} className="px-3 py-3">
                <p className="text-sm font-medium">{item.title}</p>
                <p className="text-xs text-ink-faint">
                  {new Date(item.timestamp).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
