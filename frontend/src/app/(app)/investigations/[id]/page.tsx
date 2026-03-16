import { InvestigationDetail } from "@/components/investigation/InvestigationDetail";

export default async function InvestigationPage({ params }: { params: Promise<{ id: string }> }) {
  const resolved = await params;
  const id = Number(resolved.id);
  if (Number.isNaN(id)) {
    return <div className="panel error">ID inv�lido.</div>;
  }
  return <InvestigationDetail investigationId={id} />;
}
