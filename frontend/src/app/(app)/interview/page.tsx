"use client";

import { useState, Suspense } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Job, InterviewPrep } from "@/types";
import { ChevronDown, ChevronUp, AlertCircle, BookOpen } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";

const CATEGORY_COLORS: Record<string, string> = {
  technical: "bg-accent/10 text-accent",
  behavioral: "bg-purple-500/10 text-purple-400",
  system_design: "bg-blue-500/10 text-blue-400",
  java: "bg-orange-500/10 text-orange-400",
  spring: "bg-green-500/10 text-green-400",
  default: "bg-line/60 text-ink-muted",
};

function getCategoryStyle(cat: string) {
  const key = cat.toLowerCase().replace(/\s+/g, "_");
  return CATEGORY_COLORS[key] ?? CATEGORY_COLORS.default;
}

type Critique = { score: number; strengths: string[]; improvements: string[]; example_answer: string };

function QuestionCard({
  q,
  i,
  role,
}: {
  q: { question: string; hint: string | null; category: string };
  i: number;
  role: string;
}) {
  const [open, setOpen] = useState(false);
  const [answer, setAnswer] = useState("");
  const critique = useMutation({
    mutationFn: () =>
      api<Critique>("/ai/interview-critique", {
        method: "POST",
        body: JSON.stringify({ question: q.question, answer, role }),
      }),
  });
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: i * 0.04 }}
      className="glass-panel overflow-hidden"
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-start justify-between gap-4 p-4 text-left"
      >
        <div className="flex items-start gap-3">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent/15 text-[11px] font-bold text-accent mt-0.5">
            {i + 1}
          </span>
          <div>
            <span className={`mb-1 inline-block rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${getCategoryStyle(q.category)}`}>
              {q.category}
            </span>
            <p className="text-sm font-medium">{q.question}</p>
          </div>
        </div>
        {q.hint && (open ? <ChevronUp className="h-4 w-4 shrink-0 text-ink-faint" /> : <ChevronDown className="h-4 w-4 shrink-0 text-ink-faint" />)}
      </button>
      <AnimatePresence>
        {open && q.hint && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="border-t border-line/60 px-4 py-3 ml-9">
              <p className="text-xs font-semibold text-ink-faint uppercase tracking-wide mb-1.5">Hint</p>
              <p className="text-sm text-ink-muted leading-relaxed">{q.hint}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      <div className="border-t border-line/60 p-4 sm:ml-9">
        <textarea
          className="input-field min-h-28 resize-y"
          value={answer}
          onChange={(event) => setAnswer(event.target.value)}
          placeholder="Type or paste your answer, then get a concise critique…"
        />
        <button
          type="button"
          className="btn-primary mt-2"
          disabled={critique.isPending || answer.trim().length < 20}
          onClick={() => critique.mutate()}
        >
          {critique.isPending ? "Reviewing…" : "Critique my answer"}
        </button>
        {critique.data && (
          <div className="mt-3 space-y-2 rounded-xl bg-canvas/50 p-3 text-sm">
            <p className="font-semibold text-accent">{critique.data.score}/100</p>
            <p className="text-success">{critique.data.strengths.join(" ")}</p>
            <p className="text-warning">{critique.data.improvements.join(" ")}</p>
            <p className="text-xs text-ink-muted">
              <span className="font-semibold">Stronger structure:</span> {critique.data.example_answer}
            </p>
          </div>
        )}
        {critique.isError && <p className="mt-2 text-xs text-danger">{(critique.error as Error).message}</p>}
      </div>
    </motion.div>
  );
}

function InterviewContent() {
  const params = useSearchParams();
  const jobId = params.get("job_id");
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [role, setRole] = useState("Java");

  const job = useQuery<Job>({
    queryKey: ["job", jobId],
    queryFn: () => api<Job>(`/jobs/${jobId}`),
    enabled: !!jobId,
  });

  const prep = useQuery<InterviewPrep>({
    queryKey: ["interview-prep", jobId, role],
    queryFn: () =>
      api<InterviewPrep>(
        `/ai/interview-prep${jobId ? `?job_id=${jobId}` : `?role=${encodeURIComponent(role)}`}`,
      ),
    retry: 1,
  });

  if (prep.isLoading) {
    return (
      <div className="space-y-3">
        <div className="skeleton h-12 w-full" />
        {[1, 2, 3, 4].map((i) => <div key={i} className="skeleton h-16 w-full" />)}
      </div>
    );
  }

  if (prep.isError || !prep.data) {
    return (
      <div className="glass-panel p-8 flex items-start gap-3 text-sm text-danger">
        <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
        <div>
          <p className="font-medium">Could not load interview prep</p>
          <p className="mt-1 text-xs text-ink-muted">{(prep.error as Error)?.message}</p>
        </div>
      </div>
    );
  }

  const categories = ["all", ...Array.from(new Set(prep.data.questions.map((q) => q.category)))];
  const filtered = activeCategory === "all"
    ? prep.data.questions
    : prep.data.questions.filter((q) => q.category === activeCategory);

  return (
    <div className="space-y-6">
      {/* Context */}
      {jobId && job.data && (
        <div className="glass-panel p-4 flex items-center gap-3">
          <BookOpen className="h-5 w-5 text-accent shrink-0" />
          <div>
            <p className="text-sm font-medium">{job.data.title}</p>
            <p className="text-xs text-ink-muted">{job.data.company?.name}</p>
          </div>
        </div>
      )}

      {/* Topics */}
      {!jobId && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {["Java", "Python", "AI", "QA", "Project Management"].map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => {
                setRole(item);
                setActiveCategory("all");
              }}
              className={`shrink-0 rounded-xl px-3 py-2 text-xs font-medium ${
                role === item ? "bg-accent text-white" : "btn-ghost"
              }`}
            >
              {item}
            </button>
          ))}
        </div>
      )}
      {prep.data.topics && prep.data.topics.length > 0 && (
        <div className="glass-panel p-5">
          <h3 className="font-semibold text-sm mb-3">Key Topics to Prepare</h3>
          <div className="flex flex-wrap gap-1.5">
            {prep.data.topics.map((t) => (
              <span key={t} className="rounded-lg bg-accent/10 px-2.5 py-1 text-xs font-medium text-accent">
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Category filter */}
      <div className="flex flex-wrap gap-2">
        {categories.map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setActiveCategory(cat)}
            className={`rounded-xl px-3 py-1.5 text-xs font-medium transition capitalize ${
              activeCategory === cat
                ? "bg-accent text-accent-foreground"
                : "btn-ghost !px-3 !py-1.5"
            }`}
          >
            {cat === "all" ? `All (${prep.data!.questions.length})` : cat}
          </button>
        ))}
      </div>

      {/* Questions */}
      <div className="space-y-2">
        {filtered.map((q, i) => (
          <QuestionCard key={`${role}-${i}`} q={q} i={i} role={role} />
        ))}
      </div>

      {jobId && (
        <div className="flex flex-wrap gap-3 pt-2">
          <Link href={`/resume/match?job_id=${jobId}`} className="btn-ghost text-xs">
            View Match Score
          </Link>
          <Link href={`/skill-gap?job_id=${jobId}`} className="btn-ghost text-xs">
            Skill Gap Analysis
          </Link>
        </div>
      )}
    </div>
  );
}

export default function InterviewPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6 animate-fade-up">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Interview Prep</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Practice Java, Python, AI, QA, and project management interviews, then get feedback on your answer.
        </p>
      </div>
      <Suspense fallback={<div className="skeleton h-64 w-full" />}>
        <InterviewContent />
      </Suspense>
    </div>
  );
}
