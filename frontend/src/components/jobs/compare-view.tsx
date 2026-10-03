"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { LiveView } from "@/types";
import {
  CheckCircle, XCircle, Building2, FileText, GitCompare, AlertCircle,
} from "lucide-react";
import Link from "next/link";

function HighlightedText({
  text,
  highlight,
  highlightClass,
}: {
  text: string;
  highlight: string[];
  highlightClass: string;
}) {
  if (!highlight.length) return <span>{text}</span>;

  // Build a regex with a single capturing group so split() interleaves matches
  const escaped = highlight.map((h) => h.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const regex = new RegExp(`\\b(${escaped.join("|")})\\b`, "gi");

  // split() with a capturing group produces: [non-match, match, non-match, match, ...]
  const parts = text.split(regex);
  return (
    <>
      {parts.map((part, i) =>
        part && i % 2 === 1 ? (
          <mark key={i} className={`rounded px-0.5 ${highlightClass} not-italic`}>
            {part}
          </mark>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </>
  );
}

export function CompareView({ jobId }: { jobId: string }) {
  const { data, isLoading, isError, error } = useQuery<LiveView>({
    queryKey: ["live-view", jobId],
    queryFn: () => api<LiveView>(`/jobs/${jobId}/live-view`),
    retry: 1,
  });

  if (isLoading) {
    return (
      <div className="mx-auto max-w-6xl space-y-6 animate-fade-up">
        <div className="skeleton h-12 w-64" />
        <div className="grid gap-4 md:grid-cols-2">
          <div className="skeleton h-[600px] w-full" />
          <div className="skeleton h-[600px] w-full" />
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="mx-auto max-w-6xl space-y-6 animate-fade-up">
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Live Compare</h1>
        </div>
        <div className="glass-panel p-8 flex items-start gap-3 text-sm text-danger">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Could not load comparison</p>
            <p className="mt-1 text-xs text-ink-muted">
              {(error as Error)?.message ?? "Make sure you have a primary resume uploaded."}
            </p>
            <Link href="/resume" className="mt-2 inline-block text-accent text-xs hover:underline">
              Upload a resume →
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const { job, resume, matching_skills, missing_skills, matching_keywords } = data;

  const jobText = [
    job.description,
    job.requirements,
    job.preferred_skills,
    job.responsibilities,
  ]
    .filter(Boolean)
    .join("\n\n");

  const resumeText = resume?.raw_text ?? "";

  return (
    <div className="mx-auto max-w-7xl space-y-6 animate-fade-up">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <GitCompare className="h-5 w-5 text-accent" />
            <h1 className="font-display text-2xl font-semibold tracking-tight">Live Compare</h1>
          </div>
          <p className="text-sm text-ink-muted">
            {job.title} · {job.company?.name}
          </p>
        </div>
        <div className="flex gap-2">
          <Link href={`/jobs/${jobId}`} className="btn-ghost text-sm">← Back to Job</Link>
          <Link href={`/resume/match?job_id=${jobId}`} className="btn-primary text-sm">Full Match Analysis</Link>
        </div>
      </div>

      {/* Skills legend */}
      <div className="glass-panel p-4 flex flex-wrap gap-4 text-xs">
        <div className="flex items-center gap-1.5">
          <div className="h-3 w-3 rounded bg-success/30 border border-success/50" />
          <span className="text-ink-muted">Matching skill/keyword</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-3 w-3 rounded bg-danger/30 border border-danger/50" />
          <span className="text-ink-muted">Missing from resume</span>
        </div>
      </div>

      {/* Skill chips row */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="glass-panel p-4 space-y-2">
          <h3 className="text-xs font-semibold text-ink-faint uppercase tracking-wide">Matching Skills</h3>
          <div className="flex flex-wrap gap-1.5">
            {matching_skills.length > 0 ? (
              matching_skills.map((s) => (
                <span key={s} className="inline-flex items-center gap-1 rounded-lg bg-success/10 px-2.5 py-1 text-xs font-medium text-success">
                  <CheckCircle className="h-3 w-3" />{s}
                </span>
              ))
            ) : (
              <p className="text-xs text-ink-faint">No matching skills detected</p>
            )}
          </div>
        </div>
        <div className="glass-panel p-4 space-y-2">
          <h3 className="text-xs font-semibold text-ink-faint uppercase tracking-wide">Missing Skills</h3>
          <div className="flex flex-wrap gap-1.5">
            {missing_skills.length > 0 ? (
              missing_skills.map((s) => (
                <span key={s} className="inline-flex items-center gap-1 rounded-lg bg-danger/10 px-2.5 py-1 text-xs font-medium text-danger">
                  <XCircle className="h-3 w-3" />{s}
                </span>
              ))
            ) : (
              <p className="text-xs text-ink-faint">No missing skills!</p>
            )}
          </div>
        </div>
      </div>

      {/* Side-by-side text */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Job description */}
        <div className="glass-panel overflow-hidden">
          <div className="flex items-center gap-2 border-b border-line/60 px-5 py-3">
            <Building2 className="h-4 w-4 text-accent" />
            <h2 className="font-semibold text-sm">Job Description</h2>
          </div>
          <div className="h-[500px] overflow-y-auto p-5">
            {jobText ? (
              <div className="whitespace-pre-wrap text-sm leading-relaxed text-ink-muted">
                <HighlightedText
                  text={jobText}
                  highlight={[...matching_skills, ...matching_keywords]}
                  highlightClass="bg-success/20 text-success"
                />
              </div>
            ) : job.description ? (
              <div
                className="text-sm leading-relaxed text-ink-muted [&_ul]:list-disc [&_ul]:pl-5"
                dangerouslySetInnerHTML={{ __html: job.description }}
              />
            ) : (
              <p className="text-sm text-ink-faint">No description available.</p>
            )}
          </div>
        </div>

        {/* Resume */}
        <div className="glass-panel overflow-hidden">
          <div className="flex items-center gap-2 border-b border-line/60 px-5 py-3">
            <FileText className="h-4 w-4 text-accent" />
            <h2 className="font-semibold text-sm">
              Your Resume
              {resume?.filename && (
                <span className="ml-2 text-xs text-ink-faint font-normal">({resume.filename})</span>
              )}
            </h2>
          </div>
          <div className="h-[500px] overflow-y-auto p-5">
            {resumeText ? (
              <div className="whitespace-pre-wrap text-sm leading-relaxed text-ink-muted font-mono">
                <HighlightedText
                  text={resumeText}
                  highlight={matching_skills}
                  highlightClass="bg-success/20 text-success"
                />
              </div>
            ) : resume ? (
              <div className="space-y-4">
                {resume.parsed_skills && resume.parsed_skills.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-ink-faint uppercase tracking-wide mb-2">Skills</p>
                    <div className="flex flex-wrap gap-1.5">
                      {resume.parsed_skills.map((s) => (
                        <span
                          key={s}
                          className={`rounded-lg px-2.5 py-1 text-xs font-medium ${
                            matching_skills.some((m) => m.toLowerCase() === s.toLowerCase())
                              ? "bg-success/10 text-success"
                              : "bg-line/40 text-ink-muted"
                          }`}
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {resume.parsed_experience && (
                  <div>
                    <p className="text-xs font-semibold text-ink-faint uppercase tracking-wide mb-2">Experience</p>
                    <p className="text-sm text-ink-muted whitespace-pre-wrap">{resume.parsed_experience}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="mx-auto mb-3 h-8 w-8 text-ink-faint" />
                <p className="text-sm text-ink-muted">No primary resume found</p>
                <Link href="/resume" className="btn-primary mt-4 inline-flex text-xs">
                  Upload Resume
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Action links */}
      <div className="flex flex-wrap gap-3">
        <Link href={`/skill-gap?job_id=${jobId}`} className="btn-primary text-sm">
          View Skill Gap Plan
        </Link>
        <Link href={`/resume/optimizer?job_id=${jobId}`} className="btn-ghost text-sm">
          Optimize Resume
        </Link>
        <Link href={`/cover-letter?job_id=${jobId}`} className="btn-ghost text-sm">
          Generate Cover Letter
        </Link>
      </div>
    </div>
  );
}
