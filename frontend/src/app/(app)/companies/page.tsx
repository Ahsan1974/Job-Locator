"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Building2 } from "lucide-react";
import { api } from "@/lib/api";

type Company = {
  id: string;
  name: string;
  slug: string;
  logo_url: string | null;
  industry: string | null;
  company_size: string | null;
  headquarters_country: string | null;
  offers_visa_sponsorship: boolean | null;
  open_positions: number;
};

export default function CompaniesPage() {
  const companies = useQuery({
    queryKey: ["companies"],
    queryFn: () => api<Company[]>("/companies?limit=100"),
  });

  const withJobs = (companies.data || []).filter((c) => c.open_positions > 0);
  const withoutJobs = (companies.data || []).filter((c) => c.open_positions === 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Companies</h1>
        <p className="mt-1 text-sm text-ink-muted">
          {withJobs.length} companies with active Java roles
        </p>
      </div>

      {companies.isError && (
        <div className="glass-panel p-6 text-sm text-danger">
          Failed to load companies. Check that the API is running.
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {withJobs.map((c) => (
          <Link
            key={c.id}
            href={`/companies/${c.slug}`}
            className="glass-panel p-5 transition hover:border-accent/30"
          >
            <div className="flex items-start gap-3">
              <div className="rounded-xl bg-accent/15 p-2.5 text-accent">
                <Building2 className="h-4 w-4" />
              </div>
              <div>
                <h2 className="font-semibold">{c.name}</h2>
                <p className="text-xs text-ink-muted">
                  {[c.industry, c.headquarters_country].filter(Boolean).join(" · ") || "Technology"}
                </p>
                <p className="mt-2 text-sm text-accent">{c.open_positions} open roles</p>
                {c.offers_visa_sponsorship && (
                  <span className="mt-2 inline-block rounded-md bg-success/15 px-2 py-0.5 text-[10px] text-success">
                    Visa sponsorship
                  </span>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>

      {!companies.isLoading && withJobs.length === 0 && (
        <div className="glass-panel p-8 text-center text-sm text-ink-muted">
          No companies with open roles yet — click <strong>Refresh</strong> in the top bar to load
          jobs from Jooble and other sources.
        </div>
      )}

      {withoutJobs.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-medium text-ink-faint">Other companies (no active roles)</h2>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 opacity-60">
            {withoutJobs.slice(0, 12).map((c) => (
              <Link key={c.id} href={`/companies/${c.slug}`} className="glass-panel p-4">
                <p className="font-medium text-sm">{c.name}</p>
                <p className="text-xs text-ink-faint">0 open roles</p>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
