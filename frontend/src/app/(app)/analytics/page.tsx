"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { AnalyticsOverview } from "@/types";
import { useTheme } from "next-themes";
import { useMounted } from "@/hooks/use-mounted";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from "recharts";
import { BarChart3, AlertCircle } from "lucide-react";

const STATUS_COLORS: Record<string, string> = {
  saved: "#64748b",
  applied: "#3b82f6",
  screening: "#f59e0b",
  interview: "#8b5cf6",
  offer: "#10b981",
  rejected: "#ef4444",
  withdrawn: "#6b7280",
};

const PIE_COLORS = ["#2dd4bf", "#3b82f6", "#8b5cf6", "#f59e0b", "#10b981", "#ef4444", "#f97316"];

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="glass-panel p-6 space-y-4">
      <h3 className="font-display text-base font-semibold">{title}</h3>
      {children}
    </div>
  );
}

export default function AnalyticsPage() {
  const { theme } = useTheme();
  const mounted = useMounted();
  const isDark = theme === "dark";

  const { data, isLoading, isError } = useQuery<AnalyticsOverview>({
    queryKey: ["analytics-overview"],
    queryFn: () => api<AnalyticsOverview>("/analytics/overview"),
    retry: 1,
  });

  const gridColor = isDark ? "rgba(30,41,59,0.8)" : "rgba(226,232,240,0.8)";
  const tickColor = isDark ? "#64748b" : "#94a3b8";
  const tooltipStyle = {
    background: isDark ? "#0f1624" : "#fff",
    border: "1px solid rgba(30,41,59,0.5)",
    borderRadius: "12px",
    fontSize: "12px",
    color: isDark ? "#e8eef8" : "#0f172a",
  };

  if (!mounted || isLoading) {
    return (
      <div className="mx-auto max-w-5xl space-y-6 animate-fade-up">
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Analytics</h1>
          <p className="mt-1 text-sm text-ink-muted">Your job search performance at a glance.</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {[1, 2, 3, 4].map((i) => <div key={i} className="skeleton h-64 w-full" />)}
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="mx-auto max-w-5xl space-y-6 animate-fade-up">
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Analytics</h1>
        </div>
        <div className="glass-panel p-8 flex items-start gap-3 text-sm text-danger">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Could not load analytics</p>
            <p className="mt-1 text-xs text-ink-muted">Apply to some jobs to start building your dashboard.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 animate-fade-up">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Analytics</h1>
        <p className="mt-1 text-sm text-ink-muted">Your job search performance at a glance.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Applications over time */}
        {data.applications_over_time?.length > 0 && (
          <ChartCard title="Applications Over Time">
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={data.applications_over_time} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="appGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2dd4bf" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#2dd4bf" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: tickColor }} />
                <YAxis tick={{ fontSize: 10, fill: tickColor }} allowDecimals={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Area type="monotone" dataKey="count" stroke="#2dd4bf" fill="url(#appGrad)" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
        )}

        {/* Jobs by country */}
        {data.jobs_by_country?.length > 0 && (
          <ChartCard title="Jobs by Country">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={data.jobs_by_country.slice(0, 8)} margin={{ top: 4, right: 8, left: -20, bottom: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis dataKey="country" tick={{ fontSize: 10, fill: tickColor }} angle={-30} textAnchor="end" interval={0} />
                <YAxis tick={{ fontSize: 10, fill: tickColor }} allowDecimals={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                  {data.jobs_by_country.slice(0, 8).map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        )}

        {/* Tech demand */}
        {data.tech_demand?.length > 0 && (
          <ChartCard title="Technology Demand">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={data.tech_demand.slice(0, 10)} layout="vertical" margin={{ top: 4, right: 12, left: 60, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis type="number" tick={{ fontSize: 10, fill: tickColor }} allowDecimals={false} />
                <YAxis type="category" dataKey="technology" tick={{ fontSize: 10, fill: tickColor }} width={60} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="count" fill="#2dd4bf" radius={[0, 4, 4, 0]}>
                  {data.tech_demand.slice(0, 10).map((_, i) => (
                    <Cell key={i} fill={`hsl(${175 + i * 10}, 65%, ${isDark ? "55%" : "40%"})`} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        )}

        {/* Match distribution */}
        {data.match_distribution?.length > 0 && (
          <ChartCard title="Match Score Distribution">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={data.match_distribution}
                  dataKey="count"
                  nameKey="range"
                  cx="50%"
                  cy="50%"
                  outerRadius={75}
                  label={(props) => {
                    const entry = props as { range?: string; percent?: number };
                    return `${entry.range ?? ""} (${((entry.percent ?? 0) * 100).toFixed(0)}%)`;
                  }}
                  labelLine={false}
                >
                  {data.match_distribution.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>
        )}

        {/* Status breakdown */}
        {data.status_breakdown?.length > 0 && (
          <ChartCard title="Application Status Breakdown">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={data.status_breakdown}
                  dataKey="count"
                  nameKey="status"
                  cx="50%"
                  cy="50%"
                  outerRadius={70}
                  innerRadius={35}
                >
                  {data.status_breakdown.map((entry, i) => (
                    <Cell key={i} fill={STATUS_COLORS[entry.status] ?? PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} formatter={(v, n) => [v, String(n)]} />
                <Legend
                  iconType="circle"
                  iconSize={8}
                  formatter={(value) => <span style={{ fontSize: 11, color: tickColor }}>{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>
        )}
      </div>

      {(!data.applications_over_time?.length &&
        !data.jobs_by_country?.length &&
        !data.tech_demand?.length) && (
        <div className="glass-panel p-12 text-center">
          <BarChart3 className="mx-auto mb-3 h-10 w-10 text-ink-faint" />
          <p className="text-sm font-medium">Not enough data yet</p>
          <p className="mt-1 text-xs text-ink-faint">
            Apply to jobs and track applications to build your analytics dashboard.
          </p>
        </div>
      )}
    </div>
  );
}
