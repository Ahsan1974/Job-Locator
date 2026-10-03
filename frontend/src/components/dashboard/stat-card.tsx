"use client";

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  index = 0,
  accent,
}: {
  label: string;
  value: string | number;
  hint?: string;
  icon: LucideIcon;
  index?: number;
  accent?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.4 }}
      className={cn(
        "glass-panel relative overflow-hidden p-4 transition hover:-translate-y-0.5 hover:border-accent/25",
        accent && "border-accent/30 bg-accent/5",
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-ink-muted">{label}</p>
          <p className="mt-1 font-display text-2xl font-semibold tracking-tight">{value}</p>
          {hint && <p className="mt-1 text-xs text-ink-muted">{hint}</p>}
        </div>
        <div className="rounded-xl bg-accent/10 p-2.5 text-accent">
          <Icon className="h-4 w-4" />
        </div>
      </div>
    </motion.div>
  );
}
