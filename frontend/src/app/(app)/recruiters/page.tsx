"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Recruiter } from "@/types";
import { Users, ExternalLink, Mail, Building2, Bell } from "lucide-react";
import { motion } from "framer-motion";
import Link from "next/link";

export default function RecruitersPage() {
  const qc = useQueryClient();
  const [notes, setNotes] = useState<Record<string, string>>({});
  const { data: recruiters, isLoading, isError, error } = useQuery<Recruiter[]>({
    queryKey: ["recruiters"],
    queryFn: () => api<Recruiter[]>("/recruiters"),
    retry: 1,
  });
  useEffect(() => {
    if (recruiters) {
      setNotes(Object.fromEntries(recruiters.map((recruiter) => [recruiter.id, recruiter.note || ""])));
    }
  }, [recruiters]);
  const saveNote = useMutation({
    mutationFn: ({ id, note }: { id: string; note: string }) =>
      api(`/recruiters/${id}/note`, { method: "PUT", body: JSON.stringify({ note }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["recruiters"] }),
  });

  const isNotFound = isError && error instanceof ApiError && error.status === 404;

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl space-y-6 animate-fade-up">
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Recruiters</h1>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {[1,2,3,4].map((i) => <div key={i} className="skeleton h-28 w-full" />)}
        </div>
      </div>
    );
  }

  if (isNotFound || !recruiters?.length) {
    return (
      <div className="mx-auto max-w-4xl space-y-6 animate-fade-up">
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Recruiters</h1>
          <p className="mt-1 text-sm text-ink-muted">Java & Spring Boot specialist recruiters.</p>
        </div>
        <div className="glass-panel p-12 text-center">
          <Users className="mx-auto mb-3 h-10 w-10 text-ink-faint" />
          <p className="text-sm font-medium">No recruiters available yet</p>
          <p className="mt-1 text-xs text-ink-faint max-w-sm mx-auto">
            The recruiter directory is being populated. In the meantime, browse companies that are actively hiring.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link href="/companies" className="btn-primary">Browse Companies</Link>
            <Link href="/jobs" className="btn-ghost">Browse Jobs</Link>
          </div>
        </div>

        {/* Helpful tips */}
        <div className="glass-panel p-6 space-y-3">
          <h3 className="font-display text-base font-semibold">Tips for finding Java recruiters</h3>
          <ul className="space-y-2">
            {[
              "Search LinkedIn for \"Java developer recruiter\" filtered by your target country",
              "Check job postings on this platform — many include direct recruiter contacts",
              "Join Java developer communities on Discord or Slack where recruiters often post",
              "Set up alerts to get notified when high-match roles are posted",
            ].map((tip) => (
              <li key={tip} className="flex items-start gap-2 text-sm text-ink-muted">
                <span className="text-accent mt-0.5">→</span>
                {tip}
              </li>
            ))}
          </ul>
          <Link href="/alerts" className="btn-ghost mt-2 inline-flex text-sm">
            <Bell className="h-4 w-4" /> Set up job alerts
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 animate-fade-up">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Recruiters</h1>
        <p className="mt-1 text-sm text-ink-muted">
          {recruiters.length} Java & Spring Boot specialist recruiters.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {recruiters.map((recruiter, i) => (
          <motion.div
            key={recruiter.id}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="glass-panel p-5"
          >
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent">
                <Users className="h-5 w-5" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-sm">{recruiter.name}</p>
                {recruiter.company && (
                  <div className="flex items-center gap-1 mt-0.5">
                    <Building2 className="h-3 w-3 text-ink-faint" />
                    <p className="text-xs text-ink-muted">{recruiter.company.name}</p>
                  </div>
                )}
                {recruiter.specialization && (
                  <p className="mt-1 text-xs text-ink-faint">{recruiter.specialization}</p>
                )}
                <div className="mt-3 flex gap-2">
                  {recruiter.email && (
                    <a
                      href={`mailto:${recruiter.email}`}
                      className="btn-ghost !px-2.5 !py-1.5 text-xs"
                    >
                      <Mail className="h-3.5 w-3.5" /> Email
                    </a>
                  )}
                  {recruiter.linkedin_url && (
                    <a
                      href={recruiter.linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-ghost !px-2.5 !py-1.5 text-xs"
                    >
                      LinkedIn <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
                <textarea
                  className="input-field mt-3 min-h-20 resize-y text-xs"
                  value={notes[recruiter.id] ?? ""}
                  onChange={(event) =>
                    setNotes((current) => ({ ...current, [recruiter.id]: event.target.value }))
                  }
                  placeholder="Private notes and follow-up details…"
                />
                <button
                  type="button"
                  className="btn-ghost mt-2 !px-2.5 !py-1.5 text-xs"
                  onClick={() => saveNote.mutate({ id: recruiter.id, note: notes[recruiter.id] || "" })}
                >
                  Save note
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

