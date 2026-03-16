"use client";

import Link from "next/link";
import { useState } from "react";

type SearchResult = {
  agencies: Array<{ id: number; name: string; type: string; city_id: number }>;
  politicians: Array<{ id: number; name: string; type: string; city_id: number | null }>;
  contracts: Array<{ id: number; name: string; type: string; agency_id: number; value: string }>;
};

export function EntitiesExplorer() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<SearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function search() {
    if (query.trim().length < 2) {
      setError("Digite pelo menos 2 caracteres.");
      return;
    }

    try {
      const response = await fetch(`/api/proxy/entities/search?query=${encodeURIComponent(query)}`, {
        cache: "no-store"
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const payload = (await response.json()) as SearchResult;
      setResult(payload);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div>
      <section className="panel">
        <h2 style={{ margin: 0, fontFamily: "var(--font-space)" }}>Exploração de Entidades</h2>
        <p className="section-subtitle">
          Busca profunda por pessoa política, órgão, fornecedor ou contrato para expandir investigação.
        </p>

        <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
          <input
            placeholder="Ex: Secretaria de Saúde, MedSupply, deputado"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <button className="btn" onClick={search}>Buscar</button>
        </div>
      </section>

      {error ? <div className="panel error">{error}</div> : null}

      {result ? (
        <section className="grid-3" style={{ marginTop: 16 }}>
          <article className="panel">
            <h3 className="section-title">Órgãos públicos</h3>
            <div className="card-list">
              {result.agencies.map((item) => (
                <Link key={item.id} className="card-item" href={`/relations?entity_type=public_agency&entity_id=${item.id}`}>
                  {item.name}
                </Link>
              ))}
            </div>
          </article>

          <article className="panel">
            <h3 className="section-title">Políticos</h3>
            <div className="card-list">
              {result.politicians.map((item) => (
                <Link key={item.id} className="card-item" href={`/relations?entity_type=politician&entity_id=${item.id}`}>
                  {item.name}
                </Link>
              ))}
            </div>
          </article>

          <article className="panel">
            <h3 className="section-title">Contratos</h3>
            <div className="card-list">
              {result.contracts.map((item) => (
                <article className="card-item" key={item.id}>
                  <strong>{item.name}</strong>
                  <p className="muted" style={{ margin: "6px 0 0" }}>Valor: {item.value}</p>
                </article>
              ))}
            </div>
          </article>
        </section>
      ) : null}
    </div>
  );
}

