import { CompanyDetailView } from "@/components/companies/company-detail-view";

export default async function CompanyDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return <CompanyDetailView slug={slug} />;
}
