"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Alert } from "@/types";
import { Bell, Plus, Trash2, ToggleLeft, ToggleRight, AlertCircle, X, Check } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { formatRelativeDate } from "@/lib/utils";

const CHANNELS = ["email", "dashboard", "discord", "telegram"];
const WORK_MODES = ["remote", "hybrid", "on-site"];
const COUNTRIES = ["United States", "Germany", "Netherlands", "United Kingdom", "Canada", "Poland", "Remote"];

type AlertForm = {
  name: string;
  keywords: string;
  countries: string[];
  work_modes: string[];
  min_salary: string;
  channels: string[];
};

const DEFAULT_FORM: AlertForm = {
  name: "",
  keywords: "",
  countries: [],
  work_modes: [],
  min_salary: "",
  channels: ["dashboard"],
};

export default function AlertsPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingAlert, setEditingAlert] = useState<Alert | null>(null);
  const [form, setForm] = useState<AlertForm>(DEFAULT_FORM);

  const { data: alerts, isLoading } = useQuery<Alert[]>({
    queryKey: ["alerts"],
    queryFn: () => api<Alert[]>("/alerts"),
  });

  const createAlert = useMutation({
    mutationFn: (payload: Partial<Alert>) =>
      api<Alert>("/alerts", { method: "POST", body: JSON.stringify(payload) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["alerts"] });
      setShowForm(false);
      setForm(DEFAULT_FORM);
    },
  });

  const updateAlert = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<Alert> }) =>
      api<Alert>(`/alerts/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["alerts"] });
      setEditingAlert(null);
      setShowForm(false);
      setForm(DEFAULT_FORM);
    },
  });

  const deleteAlert = useMutation({
    mutationFn: (id: string) => api(`/alerts/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });

  const toggleActive = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      api(`/alerts/${id}`, { method: "PATCH", body: JSON.stringify({ is_active: active }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });

  function openCreate() {
    setEditingAlert(null);
    setForm(DEFAULT_FORM);
    setShowForm(true);
  }

  function openEdit(alert: Alert) {
    setEditingAlert(alert);
    setForm({
      name: alert.name,
      keywords: alert.keywords.join(", "),
      countries: alert.countries,
      work_modes: alert.work_modes,
      min_salary: alert.min_salary?.toString() ?? "",
      channels: alert.channels,
    });
    setShowForm(true);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload: Partial<Alert> = {
      name: form.name,
      keywords: form.keywords.split(",").map((k) => k.trim()).filter(Boolean),
      countries: form.countries,
      work_modes: form.work_modes,
      min_salary: form.min_salary ? Number(form.min_salary) : null,
      channels: form.channels,
    };
    if (editingAlert) {
      updateAlert.mutate({ id: editingAlert.id, payload });
    } else {
      createAlert.mutate(payload);
    }
  }

  function toggleArrayItem<T>(arr: T[], item: T): T[] {
    return arr.includes(item) ? arr.filter((x) => x !== item) : [...arr, item];
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 animate-fade-up">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Alerts</h1>
          <p className="mt-1 text-sm text-ink-muted">
            Get notified via email, Discord, or Telegram when high-match Java roles appear.
          </p>
        </div>
        <button type="button" onClick={openCreate} className="btn-primary shrink-0">
          <Plus className="h-4 w-4" /> New Alert
        </button>
      </div>

      {/* Form */}
      <AnimatePresence>
        {showForm && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="glass-panel p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold">{editingAlert ? "Edit Alert" : "Create Alert"}</h2>
              <button type="button" onClick={() => setShowForm(false)} className="btn-ghost !p-1.5">
                <X className="h-4 w-4" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-ink-faint uppercase tracking-wide mb-1.5">Alert Name *</label>
                <input
                  required
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  placeholder="e.g. Senior Java Backend"
                  className="input-field"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-ink-faint uppercase tracking-wide mb-1.5">Keywords (comma-separated)</label>
                <input
                  value={form.keywords}
                  onChange={(e) => setForm((f) => ({ ...f, keywords: e.target.value }))}
                  placeholder="e.g. Spring Boot, Kafka, microservices"
                  className="input-field"
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-semibold text-ink-faint uppercase tracking-wide mb-2">Countries</label>
                  <div className="flex flex-wrap gap-1.5">
                    {COUNTRIES.map((c) => (
                      <button
                        key={c}
                        type="button"
                        onClick={() => setForm((f) => ({ ...f, countries: toggleArrayItem(f.countries, c) }))}
                        className={`rounded-lg px-2 py-1 text-xs font-medium transition ${
                          form.countries.includes(c)
                            ? "bg-accent text-accent-foreground"
                            : "bg-line/40 text-ink-muted hover:bg-line/60"
                        }`}
                      >
                        {c}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-ink-faint uppercase tracking-wide mb-2">Work Mode</label>
                  <div className="flex flex-wrap gap-1.5">
                    {WORK_MODES.map((m) => (
                      <button
                        key={m}
                        type="button"
                        onClick={() => setForm((f) => ({ ...f, work_modes: toggleArrayItem(f.work_modes, m) }))}
                        className={`rounded-lg px-2 py-1 text-xs font-medium capitalize transition ${
                          form.work_modes.includes(m)
                            ? "bg-accent text-accent-foreground"
                            : "bg-line/40 text-ink-muted hover:bg-line/60"
                        }`}
                      >
                        {m}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-semibold text-ink-faint uppercase tracking-wide mb-1.5">Min Salary (USD/yr)</label>
                  <input
                    type="number"
                    value={form.min_salary}
                    onChange={(e) => setForm((f) => ({ ...f, min_salary: e.target.value }))}
                    placeholder="e.g. 80000"
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-ink-faint uppercase tracking-wide mb-2">Notification Channels</label>
                  <div className="flex flex-wrap gap-1.5">
                    {CHANNELS.map((c) => (
                      <button
                        key={c}
                        type="button"
                        onClick={() => setForm((f) => ({ ...f, channels: toggleArrayItem(f.channels, c) }))}
                        className={`rounded-lg px-2 py-1 text-xs font-medium capitalize transition ${
                          form.channels.includes(c)
                            ? "bg-accent text-accent-foreground"
                            : "bg-line/40 text-ink-muted hover:bg-line/60"
                        }`}
                      >
                        {c}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={createAlert.isPending || updateAlert.isPending}
                  className="btn-primary flex-1"
                >
                  {(createAlert.isPending || updateAlert.isPending) ? (
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-accent-foreground border-t-transparent" />
                  ) : (
                    <><Check className="h-4 w-4" /> {editingAlert ? "Save Changes" : "Create Alert"}</>
                  )}
                </button>
                <button type="button" onClick={() => setShowForm(false)} className="btn-ghost">Cancel</button>
              </div>
              {(createAlert.isError || updateAlert.isError) && (
                <div className="flex items-center gap-2 rounded-xl bg-danger/10 px-3 py-2 text-xs text-danger">
                  <AlertCircle className="h-3.5 w-3.5" />
                  {((createAlert.error || updateAlert.error) as Error)?.message}
                </div>
              )}
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Alert list */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2].map((i) => <div key={i} className="skeleton h-24 w-full" />)}
        </div>
      ) : !alerts?.length ? (
        <div className="glass-panel p-12 text-center">
          <Bell className="mx-auto mb-3 h-10 w-10 text-ink-faint" />
          <p className="text-sm font-medium">No alerts yet</p>
          <p className="mt-1 text-xs text-ink-faint">Create your first alert to get notified about matching Java roles.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert, i) => (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className={`glass-panel p-5 ${!alert.is_active ? "opacity-60" : ""}`}
            >
              <div className="flex items-start gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="font-semibold text-sm">{alert.name}</p>
                    <span className={`rounded-md px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
                      alert.is_active ? "bg-success/15 text-success" : "bg-line/60 text-ink-faint"
                    }`}>
                      {alert.is_active ? "Active" : "Paused"}
                    </span>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {alert.keywords.map((k) => (
                      <span key={k} className="rounded-lg bg-accent/10 px-2 py-0.5 text-[11px] text-accent">{k}</span>
                    ))}
                    {alert.countries.map((c) => (
                      <span key={c} className="rounded-lg bg-line/40 px-2 py-0.5 text-[11px] text-ink-muted">{c}</span>
                    ))}
                    {alert.channels.map((c) => (
                      <span key={c} className="rounded-lg bg-line/40 px-2 py-0.5 text-[11px] text-ink-faint capitalize">{c}</span>
                    ))}
                  </div>
                  <p className="mt-2 text-[11px] text-ink-faint">Created {formatRelativeDate(alert.created_at)}</p>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  <button
                    type="button"
                    onClick={() => toggleActive.mutate({ id: alert.id, active: !alert.is_active })}
                    className="btn-ghost !px-2 !py-1.5"
                    title={alert.is_active ? "Pause" : "Activate"}
                  >
                    {alert.is_active ? <ToggleRight className="h-4 w-4 text-success" /> : <ToggleLeft className="h-4 w-4" />}
                  </button>
                  <button
                    type="button"
                    onClick={() => openEdit(alert)}
                    className="btn-ghost !px-2.5 !py-1.5 text-xs"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => { if (confirm("Delete this alert?")) deleteAlert.mutate(alert.id); }}
                    className="btn-ghost !px-2 !py-1.5 text-danger hover:bg-danger/10"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
