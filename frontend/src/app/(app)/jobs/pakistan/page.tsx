import { Suspense } from "react";
import { JobsView } from "@/components/jobs/jobs-view";

export default function PakistanJobsPage() {
  return (
    <Suspense fallback={<div className="skeleton h-96 w-full" />}>
      <JobsView
        title="Pakistan Jobs"
        subtitle="Java, Python, and software roles across Pakistan"
        lockedCountry="Pakistan"
      />
    </Suspense>
  );
}
