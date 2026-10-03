import { Suspense } from "react";
import { JobsView } from "@/components/jobs/jobs-view";
import { FreelanceImporter } from "@/components/jobs/freelance-importer";

export default function FreelanceJobsPage() {
  return (
    <>
      <FreelanceImporter />
      <Suspense fallback={<div className="skeleton h-96 w-full" />}>
        <JobsView
          title="Freelance Work"
          subtitle="Software gigs from Freelancer, Fiverr, Upwork, and PeoplePerHour"
          employmentType="freelance"
          hidePostedFilter
        />
      </Suspense>
    </>
  );
}
