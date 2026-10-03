"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Briefcase,
  Sparkles,
  CalendarDays,
  MapPin,
  Wallet,
  Building2,
  Users,
  Bookmark,
  Send,
  FileText,
  Crosshair,
  Wand2,
  Mail,
  GraduationCap,
  DollarSign,
  Route,
  Bell,
  BarChart3,
  Settings,
} from "lucide-react";
import { LinkedInIcon } from "@/components/icons/linkedin-icon";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Daily briefing", icon: LayoutDashboard, section: "Workspace" },
  { href: "/jobs", label: "All Jobs", icon: Briefcase, section: "Discover" },
  { href: "/jobs/today", label: "Today's Jobs", icon: CalendarDays },
  { href: "/jobs/linkedin", label: "LinkedIn Jobs", icon: LinkedInIcon },
  { href: "/jobs/freelance", label: "Freelance Work", icon: Wallet },
  { href: "/jobs/pakistan", label: "Pakistan Jobs", icon: MapPin },
  { href: "/jobs/recommended", label: "Recommended", icon: Sparkles },
  { href: "/companies", label: "Companies", icon: Building2 },
  { href: "/recruiters", label: "Recruiters", icon: Users },
  { href: "/saved", label: "Saved Jobs", icon: Bookmark, section: "My search" },
  { href: "/applications", label: "Applied Jobs", icon: Send },
  { href: "/resume", label: "Resume", icon: FileText, section: "Career tools" },
  { href: "/resume/match", label: "Resume Match", icon: Crosshair },
  { href: "/resume/optimizer", label: "Resume Optimizer", icon: Wand2 },
  { href: "/cover-letter", label: "Cover Letter", icon: Mail },
  { href: "/interview", label: "Interview Prep", icon: GraduationCap },
  { href: "/salary", label: "Salary Insights", icon: DollarSign },
  { href: "/skill-gap", label: "Skill Gap", icon: Route },
  { href: "/alerts", label: "Alerts", icon: Bell, section: "Insights" },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
];

function isNavItemActive(pathname: string, href: string): boolean {
  if (href === "/jobs") {
    return pathname === "/jobs";
  }
  if (href === "/jobs/today") {
    return pathname === "/jobs/today";
  }
  if (href === "/jobs/linkedin") {
    return pathname === "/jobs/linkedin";
  }
  if (href === "/jobs/freelance") {
    return pathname === "/jobs/freelance";
  }
  if (href === "/jobs/pakistan") {
    return pathname === "/jobs/pakistan";
  }
  if (href === "/companies") {
    return pathname === "/companies" || pathname.startsWith("/companies/");
  }
  return pathname === href;
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="flex-1 overflow-y-auto px-3 pb-6">
      {NAV.map((item) => {
        const active = isNavItemActive(pathname, item.href);
        const Icon = item.icon;
        return (
          <div key={item.href}>
            {item.section && (
              <p className="mb-1 mt-5 px-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-faint first:mt-1">
                {item.section}
              </p>
            )}
            <Link
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={cn(
                "relative flex min-h-10 items-center gap-3 rounded-xl px-3 py-2 text-sm transition-colors duration-150",
                active
                  ? "bg-accent/12 font-semibold text-accent"
                  : "text-ink-muted hover:bg-canvas hover:text-ink",
              )}
            >
              {active && <span className="absolute left-0 h-5 w-0.5 rounded-full bg-accent" />}
              <Icon className={cn("h-[18px] w-[18px] shrink-0", active ? "opacity-100" : "opacity-75")} />
              <span className="truncate">{item.label}</span>
            </Link>
          </div>
        );
      })}
    </nav>
  );
}

export function Sidebar({
  mobileOpen = false,
  onClose,
}: {
  mobileOpen?: boolean;
  onClose?: () => void;
}) {
  return (
    <>
      <aside className="hidden w-[17rem] shrink-0 flex-col border-r border-line/80 bg-canvas-elevated lg:flex">
        <Brand />
        <NavLinks />
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/50"
            aria-label="Close menu"
            onClick={onClose}
          />
          <aside className="relative flex h-full w-[min(18rem,85vw)] flex-col border-r border-line/70 bg-canvas shadow-2xl">
            <Brand />
            <NavLinks onNavigate={onClose} />
          </aside>
        </div>
      )}
    </>
  );
}

function Brand() {
  return (
    <div className="px-5 py-5">
      <Link href="/dashboard" className="group flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent text-accent-foreground shadow-glow">
          <span className="font-display text-sm font-bold">JC</span>
        </div>
        <div>
          <div className="font-display text-base font-semibold tracking-tight">Job Hunter</div>
          <div className="text-xs text-ink-faint">Career command center</div>
        </div>
      </Link>
    </div>
  );
}
