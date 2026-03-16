"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { CollectorRun, DatasetSource } from "@/lib/types";

export function DatasetsManager() {
  const [datasets, setDatasets] = useState<DatasetSource[]>([]);
  const [runs, setRuns] = useState<CollectorRun[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    try {
      const [datasetsResponse, runsResponse] = await Promise.all([
        api.get<DatasetSource[]>("admin/datasets"),
        api.get<CollectorRun[]>("collectors/runs")
      ]);
      setDatasets(datasetsResponse);
      setRuns(runsResponse);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function toggleDataset(source: DatasetSource) {
    try {
      await api.patch(`admin/datasets/${source.source_key}`, { enabled: !source.enabled });
      setMessage(`Fonte ${source.name} atualizada.`);
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function runCollector(sourceKey: string) {
    try {
      const run = await api.post<CollectorRun>(`collectors/run/${sourceKey}`);
      setMessage(`Coletor ${sourceKey} executado: ${run.status} (${run.records_saved} salvos)`);
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div>
      <section className="panel">
        <h2 style={{ margin: 0, fontFamily: "var(--font-space)" }}>Datasets e Coleta Automática</h2>
        <p className="section-subtitle">
          Gestão de fontes oficiais, frequência de coleta, execução manual e monitoramento de ingestão.
        </p>
      </section>

      {error ? <div className="panel error">{error}</div> : null}
      {message ? <div className="panel success">{message}</div> : null}

      <section className="grid-2" style={{ marginTop: 16 }}>
        {datasets.map((dataset) => (
          <article className="panel" key={dataset.source_key}>
            <h3 className="section-title">{dataset.name}</h3>
            <p className="section-subtitle">{dataset.endpoint_url}</p>
            <p className="muted" style={{ marginTop: 8 }}>
              Frequência: {dataset.frequency} · Status: {dataset.enabled ? "ativo" : "inativo"}
            </p>
            <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
              <button className="btn secondary" onClick={() => toggleDataset(dataset)}>
                {dataset.enabled ? "Desativar" : "Ativar"}
              </button>
              <button className="btn" onClick={() => runCollector(dataset.source_key)}>
                Executar coleta
              </button>
            </div>
          </article>
        ))}
      </section>

      <section className="panel" style={{ marginTop: 16 }}>
        <h3 className="section-title">Últimas Execuções de Coletores</h3>
        <div className="card-list" style={{ marginTop: 8 }}>
          {runs.map((run) => (
            <article className="card-item" key={run.id}>
              <strong>Run #{run.id}</strong>
              <p className="muted" style={{ margin: "6px 0 0" }}>
                status={run.status} · fetched={run.records_fetched} · saved={run.records_saved}
              </p>
              {run.error_message ? <p className="error" style={{ marginTop: 8 }}>{run.error_message}</p> : null}
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

