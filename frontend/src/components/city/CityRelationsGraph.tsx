"use client";

import CytoscapeComponent from "react-cytoscapejs";

import type { CityProfile } from "@/lib/types";

function toGraph(profile: CityProfile) {
  const nodes: Array<{ data: { id: string; label: string; type: string } }> = [];
  const edges: Array<{ data: { id: string; source: string; target: string; label: string } }> = [];

  profile.public_agencies.slice(0, 8).forEach((agency) => {
    const agencyId = `agency-${agency.id}`;
    nodes.push({ data: { id: agencyId, label: agency.name, type: "agency" } });

    const contracts = profile.contracts.filter((contract) => contract.agency_id === agency.id).slice(0, 4);
    contracts.forEach((contract) => {
      const contractId = `contract-${contract.id}`;
      const supplierId = `supplier-${contract.id}`;

      nodes.push({ data: { id: contractId, label: `Contrato ${contract.id}`, type: "contract" } });
      nodes.push({ data: { id: supplierId, label: contract.supplier, type: "supplier" } });

      edges.push({ data: { id: `${agencyId}-${contractId}`, source: agencyId, target: contractId, label: "contrata" } });
      edges.push({ data: { id: `${contractId}-${supplierId}`, source: contractId, target: supplierId, label: "fornecedor" } });
    });
  });

  return [...nodes, ...edges];
}

export function CityRelationsGraph({ profile }: { profile: CityProfile }) {
  const elements = toGraph(profile);

  return (
    <div className="panel">
      <h3 className="section-title">Grafo de Relações do Território</h3>
      <p className="section-subtitle" style={{ marginBottom: 10 }}>
        Relações entre órgãos, contratos e fornecedores no território investigado.
      </p>

      <div style={{ height: 320, border: "1px solid rgba(116, 151, 255, 0.27)", borderRadius: 12, overflow: "hidden" }}>
        <CytoscapeComponent
          elements={elements}
          layout={{ name: "cose", fit: true, padding: 20 }}
          style={{ width: "100%", height: "100%" }}
          stylesheet={[
            {
              selector: "node",
              style: {
                "background-color": "#2ce0ff",
                label: "data(label)",
                color: "#d8edff",
                "font-size": 10,
                "text-wrap": "wrap",
                "text-max-width": 90
              }
            },
            {
              selector: 'node[type = "supplier"]',
              style: { "background-color": "#00ffa9" }
            },
            {
              selector: 'node[type = "contract"]',
              style: { "background-color": "#ffcb57" }
            },
            {
              selector: "edge",
              style: {
                width: 1.8,
                "line-color": "#4e86ff",
                "target-arrow-color": "#4e86ff",
                "target-arrow-shape": "triangle",
                "curve-style": "bezier",
                label: "data(label)",
                color: "#8db3ff",
                "font-size": 8
              }
            }
          ]}
        />
      </div>
    </div>
  );
}

