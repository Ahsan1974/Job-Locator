import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatSalary(
  min?: number | string | null,
  max?: number | string | null,
  currency = "USD",
): string {
  if (min == null && max == null) return "Salary not listed";
  const code = /^[A-Z]{3}$/.test(currency) ? currency : "USD";
  const fmt = (n: number) =>
    new Intl.NumberFormat("en", {
      style: "currency",
      currency: code,
      maximumFractionDigits: 0,
    }).format(n);
  const a = min != null ? Number(min) : null;
  const b = max != null ? Number(max) : null;
  if (a != null && b != null && a !== b) return `${fmt(a)} – ${fmt(b)}`;
  if (a != null) return fmt(a);
  if (b != null) return fmt(b);
  return "Salary not listed";
}

export function formatRelativeDate(value?: string | null): string {
  if (!value) return "Unknown date";
  const date = new Date(value);
  const diff = Date.now() - date.getTime();
  const days = Math.floor(diff / 86400000);
  if (days < 1) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days}d ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;
  return date.toLocaleDateString();
}
