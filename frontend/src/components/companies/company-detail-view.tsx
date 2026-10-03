"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, ExternalLink, MapPin, Stamp, Mail, NotebookPen } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { JobCard } from "@/components/jobs/job-card";
import type { Job } from "@/types";

type CompanyDetail = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  industry: string | null;
  company_size: string | null;
  website: string | null;
  logo_url: string | null;
  headquarters_country: string | null;
  headquarters_city: string | null;
  offers_visa_sponsorship: boolean | null;
  open_positions: number;
};
type CompanyWorkspace = {
  note: string;
  applications: { id: string; job_id: string; job_title: string; status: string; updated_at: string }[];
  recruiters: { id: string; name: string; email: string | null; linkedin_url: string | null; title: string | null }[];
};

export function CompanyDetailView({ slug }: { slug: string }) {
  const qc = useQueryClient();
  const [note, setNote] = useState("");
  const company = useQuery({
    queryKey: ["company", slug],
    queryFn: () => api<CompanyDetail>(`/companies/${slug}`),
  });

  const jobs = useQuery({
    queryKey: ["company-jobs", slug],
    queryFn: () => api<Job[]>(`/companies/${slug}/jobs`),
    enabled: !!slug,
  });
  const workspace = useQuery({
    queryKey: ["company-workspace", slug],
    queryFn: () => api<CompanyWorkspace>(`/companies/${slug}/workspace`),
  });
  useEffect(() => {
    if (workspace.data) setNote(workspace.data.note);
  }, [workspace.data]);
  const saveNote = useMutation({
    mutationFn: () =>
      api(`/companies/${slug}/note`, {
        method: "PUT",
        body: JSON.stringify({ note }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["company-workspace", slug] }),
  });

  if (company.isLoading) {
    return <div className="skeleton h-64 w-full" />;
  }

  if (company.isError || !company.data) {
    return (
      <div className="glass-panel p-10 text-center">
        <p className="text-danger">Company not found.</p>
        <Link href="/companies" className="btn-ghost mt-4 inline-flex">
          Back to companies
        </Link>
      </div>
    );
  }

  const c = company.data;
  const jobList = jobs.data || [];

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <Link href="/companies" className="text-sm text-accent hover:underline">
        ← All companies
      </Link>

      <div className="glass-panel p-6 md:p-8">
        <div className="flex flex-wrap items-start gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/15 text-accent">
            <Building2 className="h-7 w-7" />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="font-display text-3xl font-semibold tracking-tight">{c.name}</h1>
            <p className="mt-1 text-sm text-ink-muted">
              {[c.industry || "Technology", c.headquarters_country].filter(Boolean).join(" · ")}
            </p>
            <div className="mt-3 flex flex-wrap gap-2 text-xs">
              {c.headquarters_city && (
                <span className="inline-flex items-center gap-1 rounded-lg bg-line/40 px-2 py-1 text-ink-muted">
                  <MapPin className="h-3 w-3" />
                  {c.headquarters_city}
                  {c.headquarters_country ? `, ${c.headquarters_country}` : ""}
                </span>
              )}
              {c.company_size && (
                <span className="rounded-lg bg-line/40 px-2 py-1 text-ink-muted">{c.company_size}</span>
              )}
              {c.offers_visa_sponsorship && (
                <span className="inline-flex items-center gap-1 rounded-lg bg-success/15 px-2 py-1 text-success">
                  <Stamp className="h-3 w-3" /> Visa sponsorship
                </span>
              )}
            </div>
          </div>
          {c.website && (
            <a
              href={c.website.startsWith("http") ? c.website : `https://${c.website}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-ghost"
            >
              Website <ExternalLink className="h-4 w-4" />
            </a>
          )}
        </div>

        {c.description && (
          <p className="mt-6 text-sm leading-relaxed text-ink-muted">{c.description}</p>
        )}

        <p className="mt-6 text-lg font-semibold text-accent">
          {c.open_positions} open Java role{c.open_positions === 1 ? "" : "s"}
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="glass-panel p-5">
          <h2 className="flex items-center gap-2 font-display text-lg font-semibold">
            <NotebookPen className="h-4 w-4 text-accent" /> Private notes
          </h2>
          <textarea
            className="input-field mt-3 min-h-32 resize-y"
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Recruiter conversations, interview details, follow-up dates…"
          />
          <button className="btn-primary mt-2" onClick={() => saveNote.mutate()} disabled={saveNote.isPending}>
            {saveNote.isPending ? "Saving…" : "Save notes"}
          </button>
        </div>
        <div className="glass-panel p-5">
          <h2 className="font-display text-lg font-semibold">Recruiters & application history</h2>
          <div className="mt-3 space-y-2">
            {workspace.data?.recruiters.map((recruiter) => (
              <div key={recruiter.id} className="rounded-xl border border-line/60 p-3 text-sm">
                <p className="font-medium">{recruiter.name}</p>
                <p className="text-xs text-ink-muted">{recruiter.title}</p>
                <div className="mt-1 flex gap-3 text-xs text-accent">
                  {recruiter.email && <a href={`mailto:${recruiter.email}`}><Mail className="mr-1 inline h-3 w-3" />Email</a>}
                  {recruiter.linkedin_url && <a href={recruiter.linkedin_url} target="_blank" rel="noreferrer">LinkedIn</a>}
                </div>
              </div>
            ))}
            {workspace.data?.applications.map((application) => (
              <Link key={application.id} href={`/jobs/${application.job_id}`} className="block rounded-xl bg-line/30 p-3 text-sm hover:bg-line/50">
                <span className="font-medium">{application.job_title}</span>
                <span className="float-right capitalize text-accent">{application.status}</span>
              </Link>
            ))}
            {!workspace.isLoading && !workspace.data?.recruiters.length && !workspace.data?.applications.length && (
              <p className="text-sm text-ink-faint">No recruiter contacts or tracked applications yet.</p>
            )}
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <h2 className="font-display text-xl font-semibold">Open positions</h2>
        {jobs.isLoading &&
          [1, 2, 3].map((i) => <div key={i} className="skeleton h-36 w-full" />)}
        {jobList.map((job, i) => (
          <JobCard key={job.id} job={job} index={i} />
        ))}
        {!jobs.isLoading && jobList.length === 0 && (
          <div className="glass-panel p-8 text-center text-sm text-ink-muted">
            No active Java roles for this company right now. Click Refresh in the top bar to fetch
            latest jobs.
          </div>
        )}
      </div>
    </div>
  );
}
