"use client";

import { useAuth } from "@/providers/auth-provider";

export default function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-ink-muted">Profile and preferences</p>
      </div>
      <div className="glass-panel space-y-4 p-6">
        <div>
          <p className="text-xs text-ink-faint">Name</p>
          <p className="font-medium">{user?.full_name || "—"}</p>
        </div>
        <div>
          <p className="text-xs text-ink-faint">Email</p>
          <p className="font-medium">{user?.email}</p>
        </div>
        <div>
          <p className="text-xs text-ink-faint">Mode</p>
          <p className="font-medium">Local (no login required)</p>
        </div>
        <div>
          <p className="text-xs text-ink-faint">Theme preference</p>
          <p className="font-medium capitalize">{user?.theme}</p>
        </div>
      </div>
    </div>
  );
}
