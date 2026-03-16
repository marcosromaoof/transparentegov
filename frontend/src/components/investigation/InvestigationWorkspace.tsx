"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { City, Investigation } from "@/lib/types";

export function InvestigationWorkspace() {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [cities, setCities] = useState<City[]>([]);
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [cityId, setCityId] = useState<number | "">("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const [investigationRows, cityRows] = await Promise.all([
        api.get<Investigation[]>("investigations"),
        api.get<City[]>("territory/cities?query=")
      ]);
      setInvestigations(investigationRows);
      setCities(cityRows);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function createInvestigation() {
    if (title.trim().length < 4) {
      setError("Título deve ter pelo menos 4 caracteres.");
      return;
    }

    try {
      await api.post("investigations", {
        title: title.trim(),
        summary: summary.trim() || null,
        scope_city_id: cityId || null
      });
      setTitle("");
      setSummary("");
      setCityId("");
      setMessage("Investigação criada com sucesso.");
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div>
      <section className="panel">
        <h2 style={{ margin: 0, fontFamily: "var(--font-space)" }}>Workspace Investigativo</h2>
        <p className="section-subtitle">Monte casos investigativos com entidades, notas, análise IA e relatórios.</p>

        <div className="form-grid" style={{ marginTop: 12 }}>
          <div className="field" style={{ gridColumn: "span 2" }}>
            <label>Título da investigação</label>
            <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Ex: Gastos da saúde em Brasília" />
          </div>

          <div className="field">
            <label>Cidade (escopo)</label>
            <select value={cityId} onChange={(event) => setCityId(event.target.value ? Number(event.target.value) : "")}>
              <option value="">Sem cidade</option>
              {cities.map((city) => (
                <option key={city.id} value={city.id}>
                  {city.name}
                </option>
              ))}
            </select>
          </div>

          <div className="field" style={{ gridColumn: "span 4" }}>
            <label>Resumo inicial</label>
            <textarea value={summary} onChange={(event) => setSummary(event.target.value)} />
          </div>
        </div>

        <button className="btn" style={{ marginTop: 12 }} onClick={createInvestigation}>
          Criar investigação
        </button>
      </section>

      {message ? <div className="panel success">{message}</div> : null}
      {error ? <div className="panel error">{error}</div> : null}

      <section className="panel" style={{ marginTop: 16 }}>
        <h3 className="section-title">Investigações cadastradas</h3>
        <div className="card-list">
          {investigations.map((investigation) => (
            <article className="card-item" key={investigation.id}>
              <h4 style={{ margin: 0 }}>{investigation.title}</h4>
              <p className="muted" style={{ margin: "8px 0" }}>
                status={investigation.status} · updated={new Date(investigation.updated_at).toLocaleString("pt-BR")}
              </p>
              <p style={{ margin: 0 }}>{investigation.summary || "Sem resumo"}</p>
              <div style={{ marginTop: 10 }}>
                <Link className="btn secondary" href={`/investigations/${investigation.id}`}>
                  Abrir investigação
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

