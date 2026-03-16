import { Suspense } from "react";

import { RelationsExplorer } from "@/components/common/RelationsExplorer";

export const dynamic = "force-dynamic";

export default function RelationsPage() {
  return (
    <Suspense fallback={<div className="panel">Carregando módulo de relações...</div>}>
      <RelationsExplorer />
    </Suspense>
  );
}

