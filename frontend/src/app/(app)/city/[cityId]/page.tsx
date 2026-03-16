import { CityProfileView } from "@/components/city/CityProfileView";

export default async function CityPage({ params }: { params: Promise<{ cityId: string }> }) {
  const resolved = await params;
  const cityId = Number(resolved.cityId);
  if (Number.isNaN(cityId)) {
    return <div className="panel error">ID de cidade inv�lido.</div>;
  }

  return <CityProfileView cityId={cityId} />;
}
