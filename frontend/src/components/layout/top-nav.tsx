"use client";

import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import {
  Bell,
  Menu,
  Moon,
  Sun,
  Search,
  RefreshCw,
  Upload,
  User as UserIcon,
  Check,
  Smartphone,
} from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useMounted } from "@/hooks/use-mounted";
import { useAuth } from "@/providers/auth-provider";
import { api } from "@/lib/api";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { Notification as AppNotification } from "@/types";
import { formatRelativeDate } from "@/lib/utils";
import Link from "next/link";

export function TopNav({ onMenu }: { onMenu?: () => void }) {
  const { theme, setTheme } = useTheme();
  const mounted = useMounted();
  const { user } = useAuth();
  const router = useRouter();
  const qc = useQueryClient();
  const [query, setQuery] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission | "unsupported">("default");
  const bellRef = useRef<HTMLDivElement>(null);
  const knownNotificationIds = useRef<Set<string> | null>(null);

  const { data: notifications } = useQuery<AppNotification[]>({
    queryKey: ["notifications"],
    queryFn: () => api<AppNotification[]>("/notifications"),
    refetchInterval: 60_000,
    retry: false,
    throwOnError: false,
  });

  const unreadCount = notifications?.filter((n) => !n.is_read).length ?? 0;

  const markRead = useMutation({
    mutationFn: (id: string) =>
      api(`/notifications/${id}/read`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAllRead = useMutation({
    mutationFn: () => api("/notifications/read-all", { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  useEffect(() => {
    if (!("Notification" in window) || !("serviceWorker" in navigator)) {
      setNotificationPermission("unsupported");
      return;
    }
    setNotificationPermission(Notification.permission);
    navigator.serviceWorker.register("/sw.js").catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!notifications) return;
    if (knownNotificationIds.current === null) {
      knownNotificationIds.current = new Set(notifications.map((item) => item.id));
      return;
    }
    const fresh = notifications.filter((item) => !knownNotificationIds.current?.has(item.id));
    notifications.forEach((item) => knownNotificationIds.current?.add(item.id));
    if (Notification.permission !== "granted") return;
    navigator.serviceWorker.ready.then((registration) => {
      fresh.slice(0, 3).forEach((item) => {
        registration.showNotification(item.title, {
          body: item.message,
          icon: "/icon.svg",
          tag: item.id,
          data: { url: item.link || "/jobs/today" },
        });
      });
    });
  }, [notifications]);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (bellRef.current && !bellRef.current.contains(e.target as Node)) {
        setNotifOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  async function enablePhoneNotifications() {
    if (!("Notification" in window) || !("serviceWorker" in navigator)) return;
    const permission = await Notification.requestPermission();
    setNotificationPermission(permission);
    if (permission !== "granted") return;

    const registration = await navigator.serviceWorker.ready;
    const config = await api<{ enabled: boolean; public_key: string }>("/notifications/push/config");
    if (!config.enabled || !config.public_key) return;
    const padding = "=".repeat((4 - (config.public_key.length % 4)) % 4);
    const base64 = (config.public_key + padding).replace(/-/g, "+").replace(/_/g, "/");
    const key = Uint8Array.from(atob(base64), (char) => char.charCodeAt(0));
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: key,
    });
    await api("/notifications/push/subscribe", {
      method: "POST",
      body: JSON.stringify(subscription.toJSON()),
    });
  }

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await api("/jobs/refresh", { method: "POST" });
      router.refresh();
    } catch {
      /* toast later */
    } finally {
      setRefreshing(false);
    }
  }

  function onSearch(e: React.FormEvent) {
    e.preventDefault();
    router.push(`/jobs?q=${encodeURIComponent(query)}`);
  }

  return (
    <header className="sticky top-0 z-30 flex h-[4.5rem] items-center gap-2 border-b border-line/80 bg-canvas/90 px-3 backdrop-blur-xl sm:gap-3 sm:px-6 lg:px-8">
      <button
        type="button"
        className="btn-ghost h-10 w-10 shrink-0 !p-0 lg:hidden"
        onClick={onMenu}
        aria-label="Open menu"
      >
        <Menu className="h-5 w-5" />
      </button>
      <form onSubmit={onSearch} className="relative min-w-0 flex-1 lg:max-w-2xl">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search jobs, skills, or companies…"
          aria-label="Search all jobs"
          className="input-field border-transparent bg-canvas-elevated pl-10 shadow-sm"
        />
      </form>

      <div className="ml-auto flex items-center gap-1.5 sm:gap-2">
        <button
          type="button"
          onClick={handleRefresh}
          className="btn-ghost h-10 w-10 !p-0"
          title="Refresh jobs"
          aria-label="Refresh jobs"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
        </button>
        <button
          type="button"
          className="btn-ghost hidden h-10 gap-2 !px-3 sm:inline-flex"
          onClick={() => router.push("/resume")}
          title="Upload resume"
        >
          <Upload className="h-4 w-4" />
          <span className="hidden sm:inline">Resume</span>
        </button>

        {/* Notifications bell */}
        <div className="relative" ref={bellRef}>
          <button
            type="button"
            className="btn-ghost h-10 w-10 !p-0 relative"
            title="Notifications"
            aria-label="Notifications"
            onClick={() => setNotifOpen((v) => !v)}
          >
            <Bell className="h-4 w-4" />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-danger text-[10px] font-bold text-white">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </button>

          {notifOpen && (
            <div className="absolute right-0 top-12 z-50 w-[min(20rem,calc(100vw-1.5rem))] glass-panel overflow-hidden shadow-xl">
              <div className="flex items-center justify-between px-4 py-3 border-b border-line/60">
                <span className="text-sm font-semibold">Notifications</span>
                {unreadCount > 0 && (
                  <button
                    type="button"
                    onClick={() => markAllRead.mutate()}
                    className="text-[11px] text-accent hover:underline"
                  >
                    Mark all read
                  </button>
                )}
              </div>
              {notificationPermission !== "granted" && notificationPermission !== "unsupported" && (
                <button
                  type="button"
                  onClick={enablePhoneNotifications}
                  className="flex w-full items-center gap-2 border-b border-line/60 px-4 py-2.5 text-left text-xs text-accent hover:bg-accent/5"
                >
                  <Smartphone className="h-4 w-4" />
                  Enable phone notifications
                </button>
              )}
              <div className="max-h-72 overflow-y-auto divide-y divide-line/40">
                {!notifications?.length ? (
                  <p className="px-4 py-6 text-center text-xs text-ink-faint">
                    No notifications
                  </p>
                ) : (
                  notifications.slice(0, 10).map((n) => (
                    <div
                      key={n.id}
                      className={`flex items-start gap-3 px-4 py-3 hover:bg-canvas-elevated/60 transition ${
                        !n.is_read ? "bg-accent/5" : ""
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        {n.link ? (
                          <Link
                            href={n.link}
                            className="block text-xs font-medium hover:text-accent truncate"
                            onClick={() => setNotifOpen(false)}
                          >
                            {n.title}
                          </Link>
                        ) : (
                          <p className="text-xs font-medium truncate">{n.title}</p>
                        )}
                        <p className="text-[11px] text-ink-faint mt-0.5 line-clamp-2">{n.message}</p>
                        <p className="text-[10px] text-ink-faint mt-1">
                          {formatRelativeDate(n.created_at)}
                        </p>
                      </div>
                      {!n.is_read && (
                        <button
                          type="button"
                          onClick={() => markRead.mutate(n.id)}
                          className="shrink-0 rounded-lg p-1 text-ink-faint hover:text-accent hover:bg-accent/10 transition"
                          title="Mark as read"
                        >
                          <Check className="h-3 w-3" />
                        </button>
                      )}
                    </div>
                  ))
                )}
              </div>
              <div className="border-t border-line/60 px-4 py-2">
                <Link
                  href="/notifications"
                  className="text-[11px] text-accent hover:underline"
                  onClick={() => setNotifOpen(false)}
                >
                  View all notifications
                </Link>
              </div>
            </div>
          )}
        </div>

        <button
          type="button"
          className="btn-ghost h-10 w-10 !p-0"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          title="Toggle theme"
          aria-label="Toggle color theme"
        >
          {mounted && theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </button>
        <div className="hidden items-center gap-2 rounded-xl border border-line bg-canvas-elevated/60 px-2.5 py-1.5 sm:flex">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/20 text-accent">
            <UserIcon className="h-3.5 w-3.5" />
          </div>
          <div className="min-w-0">
            <div className="truncate text-xs font-medium">{user?.full_name || "Personal Workspace"}</div>
            <div className="truncate text-xs text-ink-faint">Local mode</div>
          </div>
        </div>
      </div>
    </header>
  );
}
