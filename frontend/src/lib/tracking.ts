import type { QueryClient } from "@tanstack/react-query";

/** Refresh dashboard + applications after tracking an apply. */
export function invalidateTrackingQueries(qc: QueryClient) {
  void qc.invalidateQueries({ queryKey: ["applications"] });
  void qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
  void qc.invalidateQueries({ queryKey: ["activity"] });
}
