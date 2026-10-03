import { Suspense } from "react";
import { JobsView } from "@/components/jobs/jobs-view";

export default function TodayJobsPage() {
  return (
    <Suspense fallback={<div className="skeleton h-96 w-full" />}>
      <JobsView
        title="Today's Jobs"
        subtitle="New Java roles added today — refreshes daily"
        addedToday
        hidePostedFilter
      />
    </Suspense>
  );
}
