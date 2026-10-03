"use client";

import { useState, Suspense } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { SalaryEstimate, SalaryInsight, Job } from "@/types";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell,
} from "recharts";
import { DollarSign, TrendingUp, AlertCircle } from "lucide-react";
import { formatSalary } from "@/lib/utils";
import { useTheme } from "next-themes";
import { useMounted } from "@/hooks/use-mounted";

const EXPERIENCE_LEVELS = ["junior", "mid", "senior", "lead", "principal"];
const COUNTRIES = ["United States", "Germany", "Netherlands", "United Kingdom", "Canada", "Australia", "Poland", "Remote"];
const COMMON_TECHS = ["Java", "Spring Boot", "Kafka", "AWS", "Kubernetes", "Microservices", "Hibernate", "PostgreSQL", "Docker", "Redis"];

function EstimatorForm({ jobId }: { jobId: string | null }) {
  const [country, setCountry] = useState("United States");
  const [level, setLevel] = useState("mid");
  const [techs, setTechs] = useState<string[]>(["Java", "Spring Boot"]);
  const [result, setResult] = useState<SalaryEstimate | null>(null);

  const jobQuery = useQuery<Job>({
    queryKey: ["job", jobId],
    queryFn: () => api<Job>(`/jobs/${jobId}`),
    enabled: !!jobId,
  });

  const estimate = useMutation({
    mutationFn: () =>
      jobId
        ? api<SalaryEstimate>(`/salary/estimate?job_id=${jobId}`)
        : api<SalaryEstimate>("/salary/estimate", {
            method: "POST",
            body: JSON.stringify({ country, experience_level: level, technologies: techs }),
          }),
    onSuccess: (data) => setResult(data),
  });

  function toggleTech(t: string) {
    setTechs((prev) => prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]);
  }

  return (
    <div className="glass-panel p-6 space-y-5">
      <h2 className="font-display text-lg font-semibold">Salary Estimator</h2>

      {jobId && jobQuery.data && (
        <div className="rounded-xl bg-accent/10 px-4 py-3 text-sm">
          <p className="text-xs text-ink-faint">Estimating for</p>
          <p className="font-medium text-accent">{jobQuery.data.title} · {jobQuery.data.company?.name}</p>
        </div>
      )}

      {!jobId && (
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-xs font-semibold text-ink-faint mb-1.5 uppercase tracking-wide">Country</label>
            <select
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="input-field"
            >
              {COUNTRIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-ink-faint mb-1.5 uppercase tracking-wide">Experience Level</label>
            <select
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              className="input-field capitalize"
            >
              {EXPERIENCE_LEVELS.map((l) => <option key={l} value={l} className="capitalize">{l}</option>)}
            </select>
          </div>
          <div className="sm:col-span-2">
            <label className="block text-xs font-semibold text-ink-faint mb-2 uppercase tracking-wide">Technologies</label>
            <div className="flex flex-wrap gap-1.5">
              {COMMON_TECHS.map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => toggleTech(t)}
                  className={`rounded-lg px-2.5 py-1 text-xs font-medium transition ${
                    techs.includes(t)
                      ? "bg-accent text-accent-foreground"
                      : "bg-line/40 text-ink-muted hover:bg-line/70"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <button
        type="button"
        onClick={() => estimate.mutate()}
        disabled={estimate.isPending}
        className="btn-primary w-full"
      >
        {estimate.isPending ? (
          <><div className="h-4 w-4 animate-spin rounded-full border-2 border-accent-foreground border-t-transparent" /> Estimating…</>
        ) : (
          <><DollarSign className="h-4 w-4" /> Get Salary Estimate</>
        )}
      </button>

      {estimate.isError && (
        <div className="flex items-start gap-2 rounded-xl bg-danger/10 px-4 py-3 text-xs text-danger">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          {(estimate.error as Error).message}
        </div>
      )}

      {result && (
        <div className="rounded-2xl border border-line/60 bg-canvas/40 p-5 space-y-4">
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="rounded-xl bg-canvas-elevated/60 p-3">
              <p className="text-[10px] text-ink-faint uppercase tracking-wide">Min</p>
              <p className="mt-1 font-display text-lg font-bold text-ink">
                {formatSalary(result.min, null, result.currency)}
              </p>
            </div>
            <div className="rounded-xl bg-accent/10 border border-accent/30 p-3">
              <p className="text-[10px] text-accent uppercase tracking-wide">Median</p>
              <p className="mt-1 font-display text-xl font-bold text-accent">
                {formatSalary(result.median, null, result.currency)}
              </p>
            </div>
            <div className="rounded-xl bg-canvas-elevated/60 p-3">
              <p className="text-[10px] text-ink-faint uppercase tracking-wide">Max</p>
              <p className="mt-1 font-display text-lg font-bold text-ink">
                {formatSalary(result.max, null, result.currency)}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 text-xs text-ink-faint">
            <span className="rounded-lg bg-line/40 px-2 py-1 capitalize">{result.experience_level}</span>
            <span className="rounded-lg bg-line/40 px-2 py-1">{result.country}</span>
            {result.technologies.map((t) => (
              <span key={t} className="rounded-lg bg-accent/10 px-2 py-1 text-accent">{t}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function InsightsChart() {
  const { theme } = useTheme();
  const mounted = useMounted();
  const isDark = theme === "dark";

  const { data: insights, isLoading, isError } = useQuery<SalaryInsight[]>({
    queryKey: ["salary-insights"],
    queryFn: () => api<SalaryInsight[]>("/salary/insights"),
    retry: 1,
  });

  if (!mounted || isLoading) return <div className="skeleton h-64 w-full" />;
  if (isError || !insights?.length) return null;

  const chartData = insights.slice(0, 12).map((i) => ({
    name: i.technology,
    salary: Math.round(i.avg_salary / 1000),
    jobs: i.job_count,
  }));

  return (
    <div className="glass-panel p-6 space-y-4">
      <div className="flex items-center gap-2">
        <TrendingUp className="h-5 w-5 text-accent" />
        <h2 className="font-display text-lg font-semibold">Technology Salary Insights</h2>
      </div>
      <p className="text-xs text-ink-faint">Average annual salary (thousands) by technology</p>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData} margin={{ top: 4, right: 8, left: -12, bottom: 40 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "rgba(30,41,59,0.8)" : "rgba(226,232,240,0.8)"} />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11, fill: isDark ? "#64748b" : "#94a3b8" }}
            angle={-35}
            textAnchor="end"
            interval={0}
          />
          <YAxis tick={{ fontSize: 11, fill: isDark ? "#64748b" : "#94a3b8" }} tickFormatter={(v) => `$${v}k`} />
          <Tooltip
            contentStyle={{
              background: isDark ? "#0f1624" : "#fff",
              border: "1px solid rgba(30,41,59,0.5)",
              borderRadius: "12px",
              fontSize: "12px",
              color: isDark ? "#e8eef8" : "#0f172a",
            }}
            formatter={(v) => [`$${Number(v)}k/yr`, "Avg Salary"]}
          />
          <Bar dataKey="salary" radius={[6, 6, 0, 0]}>
            {chartData.map((_, i) => (
              <Cell
                key={i}
                fill={`hsl(${175 + i * 8}, 70%, ${isDark ? "55%" : "40%"})`}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function SalaryPageContent() {
  const params = useSearchParams();
  const jobId = params.get("job_id");

  return (
    <div className="space-y-6">
      <EstimatorForm jobId={jobId} />
      <InsightsChart />
    </div>
  );
}

export default function SalaryPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 animate-fade-up">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Salary Insights</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Estimated salary ranges by country, experience level, and technology stack.
        </p>
      </div>
      <Suspense fallback={<div className="skeleton h-48 w-full" />}>
        <SalaryPageContent />
      </Suspense>
    </div>
  );
}
