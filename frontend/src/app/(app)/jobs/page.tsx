import { Suspense } from "react";
import { JobsView } from "@/components/jobs/jobs-view";

export default function JobsPage() {
  return (
    <Suspense fallback={<div className="skeleton h-96 w-full" />}>
      <JobsView />
    </Suspense>
  );
}
