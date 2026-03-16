"use client";

import { useMemo, useState } from "react";
import CytoscapeComponent from "react-cytoscapejs";
import { useSearchParams } from "next/navigation";

type GraphResponse = {
  nodes: Array<{ id: string; label: string; type: string; value?: string }>;
  edges: Array<{ source: string; target: string; label: string }>;
};

export function RelationsExplorer() {
  const params = useSearchParams();
  const [entityType, setEntityType] = useState(params.get("entity_type") || "public_agency");
  const [entityId, setEntityId] = useState(params.get("entity_id") || "");
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (!entityId) {
      setError("Informe o ID da entidade.");
      return;
    }

    try {
      const response = await fetch(`/api/proxy/entities/${entityType}/${entityId}/relations`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const payload = (await response.json()) as GraphResponse;
      setGraph(payload);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  const elements = useMemo(() => {
    if (!graph) {
      return [];
    }

    return [
      ...graph.nodes.map((node) => ({ data: node })),
      ...graph.edges.map((edge, index) => ({ data: { id: `${edge.source}-${edge.target}-${index}`, ...edge } }))
    ];
  }, [graph]);

  return (
    <div>
      <section className="panel">
        <h2 style={{ margin: 0, fontFamily: "var(--font-space)" }}>Relações entre Entidades</h2>
        <p className="section-subtitle">
          Expanda conexões investigativas para mapear vínculos entre órgãos, contratos, fornecedores e agentes públicos.
        </p>

        <div className="form-grid" style={{ marginTop: 12 }}>
          <div className="field">
            <label>Tipo da entidade</label>
            <select value={entityType} onChange={(event) => setEntityType(event.target.value)}>
              <option value="public_agency">Órgão público</option>
              <option value="politician">Político</option>
            </select>
          </div>
          <div className="field">
            <label>ID da entidade</label>
            <input value={entityId} onChange={(event) => setEntityId(event.target.value)} />
          </div>
        </div>

        <button className="btn" style={{ marginTop: 10 }} onClick={load}>Carregar relações</button>
      </section>

      {error ? <div className="panel error">{error}</div> : null}

      <section className="panel" style={{ marginTop: 16 }}>
        <h3 className="section-title">Grafo</h3>
        <div style={{ height: 500, border: "1px solid rgba(116, 151, 255, 0.27)", borderRadius: 12, overflow: "hidden" }}>
          <CytoscapeComponent
            elements={elements}
            layout={{ name: "cose", animate: true, fit: true, padding: 30 }}
            style={{ width: "100%", height: "100%" }}
            stylesheet={[
              {
                selector: "node",
                style: {
                  "background-color": "#2ce0ff",
                  label: "data(label)",
                  color: "#d8edff",
                  "font-size": 11,
                  "text-wrap": "wrap",
                  "text-max-width": 130
                }
              },
              {
                selector: 'node[type = "contract"]',
                style: { "background-color": "#ffcb57" }
              },
              {
                selector: 'node[type = "supplier"]',
                style: { "background-color": "#00ffa9" }
              },
              {
                selector: "edge",
                style: {
                  width: 1.6,
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
      </section>
    </div>
  );
}

