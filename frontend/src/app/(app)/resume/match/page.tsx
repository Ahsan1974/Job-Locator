"use client";

import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { MatchScore, Job } from "@/types";
import { Suspense } from "react";
import { Crosshair, AlertCircle, TrendingUp, TrendingDown, CheckCircle, XCircle } from "lucide-react";
import Link from "next/link";

function ScoreRing({ value, label, color }: { value: number; label: string; color: string }) {
  const r = 28;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - value / 100);
  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative h-16 w-16">
        <svg className="absolute inset-0 -rotate-90" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r={r} fill="none" stroke="currentColor" strokeWidth="5" className="text-line/50" />
          <circle
            cx="32" cy="32" r={r}
            fill="none" strokeWidth="5"
            stroke={color}
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 0.8s ease" }}
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-sm font-bold">{value}</span>
      </div>
      <span className="text-[11px] text-ink-faint text-center">{label}</span>
    </div>
  );
}

function MatchContent() {
  const params = useSearchParams();
  const jobId = params.get("job_id");

  const match = useQuery<MatchScore>({
    queryKey: ["match", jobId],
    queryFn: () => api<MatchScore>(`/match/job/${jobId}`),
    enabled: !!jobId,
  });

  const job = useQuery<Job>({
    queryKey: ["job", jobId],
    queryFn: () => api<Job>(`/jobs/${jobId}`),
    enabled: !!jobId,
  });

  if (!jobId) {
    return (
      <div className="mx-auto max-w-xl py-8 text-center">
        <div className="glass-panel p-10">
          <Crosshair className="mx-auto mb-4 h-10 w-10 text-ink-faint" />
          <h2 className="font-display text-xl font-semibold">Pick a job to match against</h2>
          <p className="mt-2 text-sm text-ink-muted">
            Navigate to any job posting and click the <strong>Match Score</strong> button, or
            paste a job ID in the URL: <code className="rounded bg-line/40 px-1.5 py-0.5 text-xs">/resume/match?job_id=xxx</code>
          </p>
          <Link href="/jobs" className="btn-primary mt-6 inline-flex">Browse Jobs</Link>
        </div>
      </div>
    );
  }

  if (match.isLoading || job.isLoading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-48 w-full" />
        <div className="skeleton h-32 w-full" />
        <div className="skeleton h-32 w-full" />
      </div>
    );
  }

  if (match.isError || !match.data) {
    return (
      <div className="glass-panel p-8 flex items-start gap-3 text-sm text-danger">
        <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
        <div>
          <p className="font-medium">Could not load match score</p>
          <p className="mt-1 text-xs text-ink-muted">Make sure you have a primary resume uploaded and the job exists.</p>
        </div>
      </div>
    );
  }

  const m = match.data;
  const scoreColor = m.overall >= 75 ? "#10b981" : m.overall >= 50 ? "#f59e0b" : "#ef4444";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-panel p-6">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h2 className="font-display text-xl font-semibold">{job.data?.title ?? "Job Match"}</h2>
            <p className="mt-0.5 text-sm text-ink-muted">{job.data?.company?.name}</p>
          </div>
          <div className="flex items-center gap-2 rounded-2xl border-2 px-5 py-3" style={{ borderColor: scoreColor }}>
            <span className="font-display text-3xl font-bold" style={{ color: scoreColor }}>{m.overall}</span>
            <span className="text-xs text-ink-faint">/100<br />Overall</span>
          </div>
        </div>

        {/* Score breakdown */}
        <div className="mt-6 grid grid-cols-3 gap-4 sm:grid-cols-5">
          <ScoreRing value={m.skill_match} label="Skills" color="#2dd4bf" />
          <ScoreRing value={m.experience_match} label="Experience" color="#60a5fa" />
          <ScoreRing value={m.education_match} label="Education" color="#a78bfa" />
          <ScoreRing value={m.technology_match} label="Technology" color="#fb923c" />
          <ScoreRing value={m.ats_score} label="ATS Score" color="#f472b6" />
        </div>
      </div>

      {/* Two columns */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Strengths */}
        {m.strengths.length > 0 && (
          <div className="glass-panel p-5">
            <h3 className="flex items-center gap-2 font-semibold text-sm text-success">
              <TrendingUp className="h-4 w-4" /> Strengths
            </h3>
            <ul className="mt-3 space-y-1.5">
              {m.strengths.map((s) => (
                <li key={s} className="flex items-start gap-2 text-xs text-ink-muted">
                  <CheckCircle className="h-3.5 w-3.5 shrink-0 text-success mt-0.5" />
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Weaknesses */}
        {m.weaknesses.length > 0 && (
          <div className="glass-panel p-5">
            <h3 className="flex items-center gap-2 font-semibold text-sm text-warning">
              <TrendingDown className="h-4 w-4" /> Areas to improve
            </h3>
            <ul className="mt-3 space-y-1.5">
              {m.weaknesses.map((w) => (
                <li key={w} className="flex items-start gap-2 text-xs text-ink-muted">
                  <AlertCircle className="h-3.5 w-3.5 shrink-0 text-warning mt-0.5" />
                  {w}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Matching skills */}
      {m.matching_skills.length > 0 && (
        <div className="glass-panel p-5">
          <h3 className="font-semibold text-sm mb-3">Matching Skills</h3>
          <div className="flex flex-wrap gap-1.5">
            {m.matching_skills.map((s) => (
              <span key={s} className="inline-flex items-center gap-1 rounded-lg bg-success/10 px-2.5 py-1 text-xs font-medium text-success">
                <CheckCircle className="h-3 w-3" />{s}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Missing skills */}
      {m.missing_skills.length > 0 && (
        <div className="glass-panel p-5">
          <h3 className="font-semibold text-sm mb-1">Missing Skills</h3>
          <p className="text-xs text-ink-faint mb-3">
            These skills appear in the job requirements but not in your resume.
          </p>
          <div className="flex flex-wrap gap-1.5">
            {m.missing_skills.map((s) => (
              <span key={s} className="inline-flex items-center gap-1 rounded-lg bg-danger/10 px-2.5 py-1 text-xs font-medium text-danger">
                <XCircle className="h-3 w-3" />{s}
              </span>
            ))}
          </div>
          {jobId && (
            <Link
              href={`/skill-gap?job_id=${jobId}`}
              className="btn-ghost mt-4 text-xs !px-3 !py-1.5"
            >
              View learning plan →
            </Link>
          )}
        </div>
      )}

      {/* Missing keywords */}
      {m.missing_keywords.length > 0 && (
        <div className="glass-panel p-5">
          <h3 className="font-semibold text-sm mb-3">Missing Keywords (ATS)</h3>
          <div className="flex flex-wrap gap-1.5">
            {m.missing_keywords.map((k) => (
              <span key={k} className="rounded-lg bg-warning/10 px-2.5 py-1 text-xs font-medium text-warning">
                {k}
              </span>
            ))}
          </div>
        </div>
      )}

      {jobId && (
        <div className="flex flex-wrap gap-3">
          <Link href={`/resume/optimizer?job_id=${jobId}`} className="btn-primary">
            Optimize Resume for this Job
          </Link>
          <Link href={`/cover-letter?job_id=${jobId}`} className="btn-ghost">
            Generate Cover Letter
          </Link>
          <Link href={`/jobs/${jobId}/compare`} className="btn-ghost">
            Live Side-by-Side Compare
          </Link>
        </div>
      )}
    </div>
  );
}

export default function MatchPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 animate-fade-up">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Resume Match</h1>
        <p className="mt-1 text-sm text-ink-muted">
          AI-powered scoring: how well your resume matches a job posting.
        </p>
      </div>
      <Suspense fallback={<div className="skeleton h-64 w-full" />}>
        <MatchContent />
      </Suspense>
    </div>
  );
}
