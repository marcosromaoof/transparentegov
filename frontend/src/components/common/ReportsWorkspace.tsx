"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Investigation } from "@/lib/types";

type ReportResponse = {
  investigation_id: number;
  format: "markdown" | "pdf";
  content: string;
};

export function ReportsWorkspace() {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [investigationId, setInvestigationId] = useState<number | "">("");
  const [format, setFormat] = useState<"markdown" | "pdf">("markdown");
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<Investigation[]>("investigations")
      .then(setInvestigations)
      .catch((err: Error) => setError(err.message));
  }, []);

  async function generate() {
    if (!investigationId) {
      setError("Selecione uma investigação.");
      return;
    }

    try {
      const result = await api.get<ReportResponse>(`reports/investigations/${investigationId}?format=${format}`);
      setReport(result);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div>
      <section className="panel">
        <h2 style={{ margin: 0, fontFamily: "var(--font-space)" }}>Relatórios Investigativos</h2>
        <p className="section-subtitle">Geração automática em Markdown ou PDF com base nas investigações salvas.</p>

        <div className="form-grid" style={{ marginTop: 10 }}>
          <div className="field" style={{ gridColumn: "span 2" }}>
            <label>Investigação</label>
            <select value={investigationId} onChange={(event) => setInvestigationId(event.target.value ? Number(event.target.value) : "") }>
              <option value="">Selecione</option>
              {investigations.map((item) => (
                <option key={item.id} value={item.id}>
                  #{item.id} - {item.title}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Formato</label>
            <select value={format} onChange={(event) => setFormat(event.target.value as "markdown" | "pdf") }>
              <option value="markdown">Markdown</option>
              <option value="pdf">PDF (base64)</option>
            </select>
          </div>
        </div>

        <button className="btn" style={{ marginTop: 12 }} onClick={generate}>
          Gerar relatório
        </button>
      </section>

      {error ? <div className="panel error">{error}</div> : null}

      {report ? (
        <section className="panel" style={{ marginTop: 16 }}>
          <h3 className="section-title">Saída do relatório ({report.format})</h3>
          <textarea readOnly value={report.content} style={{ minHeight: 340 }} />
        </section>
      ) : null}
    </div>
  );
}

