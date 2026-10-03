"use client";



import { useState, Suspense } from "react";

import { useQuery, useMutation } from "@tanstack/react-query";

import { useSearchParams } from "next/navigation";

import { api, API_URL } from "@/lib/api";

import type { Job, OptimizeResult } from "@/types";

import {

  Wand2,

  Copy,

  CheckCheck,

  TrendingUp,

  AlertCircle,

  Download,

  Sparkles,

  Target,

} from "lucide-react";

import { JobPicker } from "@/components/jobs/job-picker";



function SkillChips({

  label,

  skills,

  variant,

}: {

  label: string;

  skills: string[];

  variant: "match" | "gap";

}) {

  if (!skills.length) return null;

  return (

    <div>

      <p className="text-xs font-medium text-ink-faint mb-2">{label}</p>

      <div className="flex flex-wrap gap-1.5">

        {skills.map((skill) => (

          <span

            key={skill}

            className={

              variant === "match"

                ? "rounded-lg bg-success/10 px-2 py-0.5 text-[11px] text-success"

                : "rounded-lg bg-warning/10 px-2 py-0.5 text-[11px] text-warning"

            }

          >

            {skill}

          </span>

        ))}

      </div>

    </div>

  );

}



function OptimizerContent() {

  const params = useSearchParams();

  const jobId = params.get("job_id");

  const [copied, setCopied] = useState(false);

  const [downloading, setDownloading] = useState(false);

  const [result, setResult] = useState<OptimizeResult | null>(null);



  const job = useQuery<Job>({

    queryKey: ["job", jobId],

    queryFn: () => api<Job>(`/jobs/${jobId}`),

    enabled: !!jobId,

  });



  const optimize = useMutation({

    mutationFn: () =>

      api<OptimizeResult>("/ai/optimize-resume", {

        method: "POST",

        body: JSON.stringify({ job_id: jobId }),

      }),

    onSuccess: (data) => setResult(data),

  });



  function copyToClipboard() {

    if (!result?.optimized_resume) return;

    navigator.clipboard.writeText(result.optimized_resume);

    setCopied(true);

    setTimeout(() => setCopied(false), 2000);

  }



  async function downloadPdf() {

    if (!jobId) return;

    setDownloading(true);

    try {

      const res = await fetch(`${API_URL}/ai/optimize-resume/pdf`, {

        method: "POST",

        headers: { "Content-Type": "application/json" },

        body: JSON.stringify({ job_id: jobId }),

      });

      if (!res.ok) {

        const err = await res.json().catch(() => ({}));

        throw new Error(err.detail || "PDF generation failed");

      }

      const blob = await res.blob();

      const url = URL.createObjectURL(blob);

      const a = document.createElement("a");

      a.href = url;

      a.download = `tailored-resume-${jobId.slice(0, 8)}.pdf`;

      a.click();

      URL.revokeObjectURL(url);

    } catch (e) {

      alert(e instanceof Error ? e.message : "Download failed");

    } finally {

      setDownloading(false);

    }

  }



  if (!jobId) {

    return (

      <JobPicker

        title="Tailor your CV"

        description="Pick a job to generate an ATS-optimized resume tailored to that role — with keyword alignment, skills summary, and PDF download."

        basePath="/resume/optimizer"

      />

    );

  }



  const scoreDelta =

    result?.ats_score_after !== undefined && result?.ats_score_before !== undefined

      ? Math.round(result.ats_score_after - result.ats_score_before)

      : null;



  return (

    <div className="space-y-6">

      {job.data && (

        <div className="glass-panel p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">

          <div className="min-w-0">

            <p className="text-xs text-ink-faint flex items-center gap-1">

              <Target className="h-3 w-3" /> Optimizing for

            </p>

            <p className="font-semibold truncate">{job.data.title}</p>

            <p className="text-sm text-ink-muted truncate">

              {job.data.company?.name}

              {job.data.country ? ` · ${job.data.country}` : ""}

            </p>

          </div>

          <button

            type="button"

            onClick={() => optimize.mutate()}

            disabled={optimize.isPending}

            className="btn-primary shrink-0"

          >

            {optimize.isPending ? (

              <>

                <div className="h-4 w-4 animate-spin rounded-full border-2 border-accent-foreground border-t-transparent" />

                Optimizing…

              </>

            ) : (

              <>

                <Wand2 className="h-4 w-4" />

                {result ? "Re-optimize" : "Optimize Resume"}

              </>

            )}

          </button>

        </div>

      )}



      {!result && !optimize.isPending && (

        <div className="glass-panel p-6 text-center text-sm text-ink-muted">

          <Sparkles className="h-8 w-8 mx-auto mb-3 text-accent/60" />

          <p>Click <strong className="text-ink">Optimize Resume</strong> to tailor your CV with ATS keywords from this job posting.</p>

        </div>

      )}



      {optimize.isError && (

        <div className="glass-panel p-4 flex items-start gap-3 text-sm text-danger">

          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />

          <p>{(optimize.error as Error).message}</p>

        </div>

      )}



      {result && (

        <>

          {(result.ats_score_before !== undefined || result.ats_score_after !== undefined) && (

            <div className="glass-panel p-5">

              <h3 className="flex items-center gap-2 font-semibold text-sm mb-4">

                <TrendingUp className="h-4 w-4 text-success" /> ATS Score

                {scoreDelta !== null && scoreDelta > 0 && (

                  <span className="ml-auto text-xs font-normal text-success">+{scoreDelta} pts</span>

                )}

              </h3>

              <div className="flex items-center gap-4 sm:gap-6">

                <div className="text-center shrink-0">

                  <p className="font-display text-2xl font-bold text-danger">{result.ats_score_before}</p>

                  <p className="text-xs text-ink-faint">Before</p>

                </div>

                <div className="flex-1 h-2.5 rounded-full bg-line/40 relative overflow-hidden">

                  <div

                    className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-danger via-accent to-success transition-all duration-700"

                    style={{ width: `${Math.min(100, result.ats_score_after ?? 0)}%` }}

                  />

                </div>

                <div className="text-center shrink-0">

                  <p className="font-display text-2xl font-bold text-success">{result.ats_score_after}</p>

                  <p className="text-xs text-ink-faint">After</p>

                </div>

              </div>

            </div>

          )}



          {(result.matching_skills?.length || result.missing_skills?.length) && (

            <div className="glass-panel p-5 grid gap-4 sm:grid-cols-2">

              <SkillChips label="Matching skills" skills={result.matching_skills ?? []} variant="match" />

              <SkillChips label="Keywords to emphasize" skills={result.missing_skills ?? []} variant="gap" />

            </div>

          )}



          {result.improvements && result.improvements.length > 0 && (

            <div className="glass-panel p-5">

              <h3 className="font-semibold text-sm mb-3">What was improved</h3>

              <ul className="space-y-2">

                {result.improvements.map((imp, i) => (

                  <li key={i} className="flex items-start gap-2 text-sm text-ink-muted">

                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent/15 text-accent text-[10px] font-bold mt-0.5">

                      {i + 1}

                    </span>

                    {imp}

                  </li>

                ))}

              </ul>

            </div>

          )}



          <div className="glass-panel overflow-hidden">

            <div className="flex items-center justify-between border-b border-line/60 px-5 py-3 gap-2">

              <h3 className="font-semibold text-sm">Optimized Resume</h3>

              <div className="flex gap-2 shrink-0">

                <button

                  type="button"

                  onClick={downloadPdf}

                  disabled={downloading}

                  className="btn-primary !px-3 !py-1.5 text-xs"

                >

                  {downloading ? (

                    <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-accent-foreground border-t-transparent" />

                  ) : (

                    <Download className="h-3.5 w-3.5" />

                  )}

                  PDF

                </button>

                <button

                  type="button"

                  onClick={copyToClipboard}

                  className="btn-ghost !px-3 !py-1.5 text-xs"

                >

                  {copied ? (

                    <>

                      <CheckCheck className="h-3.5 w-3.5 text-success" /> Copied

                    </>

                  ) : (

                    <>

                      <Copy className="h-3.5 w-3.5" /> Copy

                    </>

                  )}

                </button>

              </div>

            </div>

            <div className="max-h-[32rem] overflow-y-auto p-5 bg-canvas/30">

              <pre className="whitespace-pre-wrap text-xs font-mono text-ink-muted leading-relaxed">

                {result.optimized_resume}

              </pre>

            </div>

          </div>

        </>

      )}

    </div>

  );

}



export default function OptimizerPage() {

  return (

    <div className="mx-auto max-w-4xl space-y-6 animate-fade-up">

      <div>

        <h1 className="font-display text-3xl font-semibold tracking-tight">Resume Optimizer</h1>

        <p className="mt-1 text-sm text-ink-muted">

          Tailor your resume to a specific job with ATS keyword alignment, skills summary, and PDF export.

        </p>

      </div>

      <Suspense fallback={<div className="skeleton h-48 w-full" />}>

        <OptimizerContent />

      </Suspense>

    </div>

  );

}


