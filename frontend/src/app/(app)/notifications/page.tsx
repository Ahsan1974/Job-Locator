"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCheck } from "lucide-react";
import Link from "next/link";

import { api } from "@/lib/api";
import type { Notification } from "@/types";
import { formatRelativeDate } from "@/lib/utils";

export default function NotificationsPage() {
  const qc = useQueryClient();
  const notifications = useQuery<Notification[]>({
    queryKey: ["notifications"],
    queryFn: () => api<Notification[]>("/notifications"),
  });
  const markAll = useMutation({
    mutationFn: () => api("/notifications/read-all", { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
  const markOne = useMutation({
    mutationFn: (id: string) => api(`/notifications/${id}/read`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Notifications</h1>
          <p className="mt-1 text-sm text-ink-muted">New roles and Job Hunter updates.</p>
        </div>
        <button
          type="button"
          className="btn-ghost shrink-0"
          disabled={markAll.isPending}
          onClick={() => markAll.mutate()}
        >
          <CheckCheck className="h-4 w-4" /> Mark all read
        </button>
      </div>

      <div className="space-y-2">
        {notifications.isLoading &&
          [1, 2, 3].map((item) => <div key={item} className="skeleton h-24 w-full" />)}
        {notifications.data?.map((item) => (
          <article
            key={item.id}
            className={`glass-panel flex items-start gap-3 p-4 ${item.is_read ? "opacity-70" : "border-accent/30"}`}
          >
            <div className="rounded-xl bg-accent/10 p-2 text-accent">
              <Bell className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              {item.link ? (
                <Link href={item.link} className="font-medium hover:text-accent">
                  {item.title}
                </Link>
              ) : (
                <p className="font-medium">{item.title}</p>
              )}
              <p className="mt-1 text-sm text-ink-muted">{item.message}</p>
              <p className="mt-2 text-xs text-ink-faint">{formatRelativeDate(item.created_at)}</p>
            </div>
            {!item.is_read && (
              <button
                type="button"
                className="btn-ghost !p-2"
                title="Mark as read"
                onClick={() => markOne.mutate(item.id)}
              >
                <CheckCheck className="h-4 w-4" />
              </button>
            )}
          </article>
        ))}
        {!notifications.isLoading && !notifications.data?.length && (
          <div className="glass-panel p-10 text-center text-sm text-ink-muted">
            No notifications yet. New job alerts will appear here.
          </div>
        )}
      </div>
    </div>
  );
}
