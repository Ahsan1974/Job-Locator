import { Suspense } from "react";
import { LinkedInJobsView } from "@/components/jobs/linkedin-jobs-view";

export default function LinkedInJobsPage() {
  return (
    <Suspense fallback={<div className="skeleton h-96 w-full" />}>
      <LinkedInJobsView />
    </Suspense>
  );
}
