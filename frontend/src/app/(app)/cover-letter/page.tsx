"use client";

import { useState, Suspense } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Job, CoverLetterResult } from "@/types";
import { Copy, CheckCheck, AlertCircle, Sparkles } from "lucide-react";
import Link from "next/link";
import { JobPicker } from "@/components/jobs/job-picker";

function CoverLetterContent() {
  const params = useSearchParams();
  const jobId = params.get("job_id");
  const [copied, setCopied] = useState(false);
  const [result, setResult] = useState<CoverLetterResult | null>(null);

  const job = useQuery<Job>({
    queryKey: ["job", jobId],
    queryFn: () => api<Job>(`/jobs/${jobId}`),
    enabled: !!jobId,
  });

  const generate = useMutation({
    mutationFn: () =>
      api<CoverLetterResult>("/ai/cover-letter", {
        method: "POST",
        body: JSON.stringify({ job_id: jobId }),
      }),
    onSuccess: (data) => setResult(data),
  });

  function copyToClipboard() {
    if (!result?.content) return;
    navigator.clipboard.writeText(result.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (!jobId) {
    return (
      <JobPicker
        title="Cover letter generator"
        description="Pick a job to generate a tailored cover letter with AI."
        basePath="/cover-letter"
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Job context card */}
      {(job.isLoading || job.data) && (
        <div className="glass-panel p-5 flex items-center justify-between gap-4 flex-wrap">
          <div>
            <p className="text-xs text-ink-faint">Generating for</p>
            {job.isLoading ? (
              <div className="skeleton h-5 w-48 mt-1" />
            ) : (
              <>
                <p className="font-semibold">{job.data?.title}</p>
                <p className="text-sm text-ink-muted">{job.data?.company?.name}</p>
              </>
            )}
          </div>
          <button
            type="button"
            onClick={() => generate.mutate()}
            disabled={generate.isPending}
            className="btn-primary shrink-0"
          >
            {generate.isPending ? (
              <>
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-accent-foreground border-t-transparent" />
                Generating…
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                {result ? "Regenerate" : "Generate Cover Letter"}
              </>
            )}
          </button>
        </div>
      )}

      {generate.isError && (
        <div className="glass-panel p-4 flex items-start gap-3 text-sm text-danger">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Generation failed</p>
            <p className="mt-0.5 text-ink-muted">{(generate.error as Error).message}</p>
            <p className="mt-1 text-xs text-ink-faint">
              Make sure you have a primary resume uploaded.{" "}
              <Link href="/resume" className="text-accent hover:underline">Go to Resume</Link>
            </p>
          </div>
        </div>
      )}

      {result && (
        <div className="glass-panel overflow-hidden">
          <div className="flex items-center justify-between border-b border-line/60 px-5 py-3">
            <div>
              <h3 className="font-semibold text-sm">Cover Letter</h3>
              {(result.job_title || result.company_name) && (
                <p className="text-xs text-ink-faint mt-0.5">
                  {[result.job_title, result.company_name].filter(Boolean).join(" · ")}
                </p>
              )}
            </div>
            <button
              type="button"
              onClick={copyToClipboard}
              className="btn-ghost !px-3 !py-1.5 text-xs"
            >
              {copied ? (
                <><CheckCheck className="h-3.5 w-3.5 text-success" /> Copied!</>
              ) : (
                <><Copy className="h-3.5 w-3.5" /> Copy</>
              )}
            </button>
          </div>
          <div className="p-6">
            <div className="whitespace-pre-wrap text-sm leading-relaxed text-ink-muted">
              {result.content}
            </div>
          </div>
        </div>
      )}

      {!generate.isPending && !result && (
        <div className="glass-panel p-6 text-center text-sm text-ink-muted">
          <Sparkles className="mx-auto mb-3 h-8 w-8 text-ink-faint" />
          <p>Click <strong>Generate Cover Letter</strong> to create a personalized letter using your primary resume.</p>
        </div>
      )}
    </div>
  );
}

export default function CoverLetterPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6 animate-fade-up">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Cover Letter</h1>
        <p className="mt-1 text-sm text-ink-muted">
          AI-generated cover letters tailored to each job posting using your primary resume.
        </p>
      </div>
      <Suspense fallback={<div className="skeleton h-48 w-full" />}>
        <CoverLetterContent />
      </Suspense>
    </div>
  );
}
