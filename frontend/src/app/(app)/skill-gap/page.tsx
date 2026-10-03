"use client";

import { Suspense } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { SkillGapItem, Job } from "@/types";
import { Clock, AlertCircle, ExternalLink, BookOpen, Code2 } from "lucide-react";
import { motion } from "framer-motion";
import Link from "next/link";
import { JobPicker } from "@/components/jobs/job-picker";

const PRIORITY_STYLE = {
  high: { badge: "bg-danger/15 text-danger", bar: "bg-danger" },
  medium: { badge: "bg-warning/15 text-warning", bar: "bg-warning" },
  low: { badge: "bg-success/15 text-success", bar: "bg-success" },
};

function SkillGapContent() {
  const params = useSearchParams();
  const jobId = params.get("job_id");

  const job = useQuery<Job>({
    queryKey: ["job", jobId],
    queryFn: () => api<Job>(`/jobs/${jobId}`),
    enabled: !!jobId,
  });

  const gap = useQuery<SkillGapItem[]>({
    queryKey: ["skill-gap", jobId],
    queryFn: () => api<SkillGapItem[]>(`/skill-gap/job/${jobId}`),
    enabled: !!jobId,
  });

  if (!jobId) {
    return (
      <JobPicker
        title="Skill gap analysis"
        description="Pick a job to see which skills you're missing and how to learn them."
        basePath="/skill-gap"
      />
    );
  }

  if (gap.isLoading) {
    return <div className="space-y-3">{[1,2,3].map(i => <div key={i} className="skeleton h-32 w-full" />)}</div>;
  }

  if (gap.isError || !gap.data) {
    return (
      <div className="glass-panel p-8 flex items-start gap-3 text-sm text-danger">
        <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
        <div>
          <p className="font-medium">Could not load skill gap analysis</p>
          <p className="mt-1 text-xs text-ink-muted">
            Ensure you have a primary resume uploaded.{" "}
            <Link href="/resume" className="text-accent hover:underline">Upload resume</Link>
          </p>
        </div>
      </div>
    );
  }

  if (!gap.data.length) {
    return (
      <div className="glass-panel p-12 text-center">
        <p className="text-success font-medium">No skill gaps found!</p>
        <p className="mt-1 text-sm text-ink-muted">Your resume appears to match all required skills for this job.</p>
      </div>
    );
  }

  const totalHours = gap.data.reduce((sum, item) => sum + item.learning_hours, 0);
  const avgImprovement = Math.round(gap.data.reduce((sum, item) => sum + item.match_improvement, 0) / gap.data.length);

  return (
    <div className="space-y-6">
      {/* Job context */}
      {job.data && (
        <div className="glass-panel p-4 flex items-center justify-between gap-4 flex-wrap">
          <div>
            <p className="text-xs text-ink-faint">Skill gap for</p>
            <p className="font-semibold">{job.data.title}</p>
            <p className="text-xs text-ink-muted">{job.data.company?.name}</p>
          </div>
          <div className="flex gap-4">
            <div className="text-center">
              <p className="font-display text-xl font-bold text-accent">{gap.data.length}</p>
              <p className="text-[11px] text-ink-faint">Missing Skills</p>
            </div>
            <div className="text-center">
              <p className="font-display text-xl font-bold text-warning">{totalHours}h</p>
              <p className="text-[11px] text-ink-faint">Learning Time</p>
            </div>
            <div className="text-center">
              <p className="font-display text-xl font-bold text-success">+{avgImprovement}%</p>
              <p className="text-[11px] text-ink-faint">Avg Improvement</p>
            </div>
          </div>
        </div>
      )}

      {/* Skill items */}
      <div className="space-y-3">
        {gap.data.map((item, i) => {
          const style = PRIORITY_STYLE[item.priority] ?? PRIORITY_STYLE.medium;
          return (
            <motion.div
              key={item.skill}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="glass-panel p-5 space-y-3"
            >
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-2.5">
                  <span className="font-semibold">{item.skill}</span>
                  <span className={`rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${style.badge}`}>
                    {item.priority} priority
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-ink-faint shrink-0">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />{item.learning_hours}h to learn
                  </span>
                  <span className="text-success font-medium">+{item.match_improvement}% match</span>
                </div>
              </div>

              {/* Progress bar for match improvement */}
              <div className="h-1.5 rounded-full bg-line/40 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${style.bar}`}
                  style={{ width: `${Math.min(item.match_improvement * 2, 100)}%` }}
                />
              </div>

              {/* Resources */}
              {item.courses && item.courses.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-ink-faint uppercase tracking-wide mb-1.5 flex items-center gap-1">
                    <BookOpen className="h-3 w-3" /> Courses
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {item.courses.map((c) => (
                      <a
                        key={c.url}
                        href={c.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 rounded-lg border border-line/60 bg-canvas/40 px-2.5 py-1 text-xs text-ink-muted hover:text-accent hover:border-accent/40 transition"
                      >
                        {c.title}
                        {c.provider && <span className="text-ink-faint">· {c.provider}</span>}
                        <ExternalLink className="h-3 w-3 shrink-0" />
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {item.projects && item.projects.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-ink-faint uppercase tracking-wide mb-1.5 flex items-center gap-1">
                    <Code2 className="h-3 w-3" /> Practice Projects
                  </p>
                  <ul className="space-y-1">
                    {item.projects.map((p) => (
                      <li key={p} className="text-xs text-ink-muted flex items-start gap-1.5">
                        <span className="text-accent mt-0.5">→</span>{p}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {item.docs && item.docs.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {item.docs.map((d) => (
                    <a
                      key={d.url}
                      href={d.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 rounded-lg border border-accent/20 bg-accent/5 px-2.5 py-1 text-xs text-accent hover:bg-accent/15 transition"
                    >
                      {d.title} <ExternalLink className="h-3 w-3" />
                    </a>
                  ))}
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      {jobId && (
        <div className="flex flex-wrap gap-3">
          <Link href={`/resume/match?job_id=${jobId}`} className="btn-ghost text-sm">
            View Full Match Score
          </Link>
          <Link href={`/resume/optimizer?job_id=${jobId}`} className="btn-primary text-sm">
            Optimize Resume
          </Link>
        </div>
      )}
    </div>
  );
}

export default function SkillGapPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 animate-fade-up">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Skill Gap Analysis</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Missing skills with learning hours, courses, and match improvement estimates.
        </p>
      </div>
      <Suspense fallback={<div className="skeleton h-64 w-full" />}>
        <SkillGapContent />
      </Suspense>
    </div>
  );
}
