"use client";

import { useEffect, useMemo, useState } from "react";

import type { City, Country, Politician, PoliticianProfile, State } from "@/lib/types";

function money(value: string | number) {
  const numeric = typeof value === "string" ? Number(value) : value;
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(numeric || 0));
}

export function EntitiesExplorer() {
  const [countries, setCountries] = useState<Country[]>([]);
  const [states, setStates] = useState<State[]>([]);
  const [cities, setCities] = useState<City[]>([]);
  const [positions, setPositions] = useState<string[]>([]);

  const [countryId, setCountryId] = useState<number | "">("");
  const [stateId, setStateId] = useState<number | "">("");
  const [cityId, setCityId] = useState<number | "">("");
  const [cityQuery, setCityQuery] = useState("");

  const [name, setName] = useState("");
  const [position, setPosition] = useState("");
  const [activeOnly, setActiveOnly] = useState(true);

  const [politicians, setPoliticians] = useState<Politician[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<PoliticianProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch("/api/proxy/territory/countries", { cache: "no-store" }).then((r) => r.json() as Promise<Country[]>),
      fetch("/api/proxy/politicians/positions", { cache: "no-store" }).then((r) => r.json() as Promise<string[]>),
    ])
      .then(([countriesRows, positionsRows]) => {
        setCountries(countriesRows);
        if (countriesRows.length === 1) {
          setCountryId(countriesRows[0].id);
        }
        setPositions(positionsRows);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!countryId) {
      setStates([]);
      setStateId("");
      setCities([]);
      setCityId("");
      return;
    }

    fetch(`/api/proxy/territory/states?country_id=${countryId}`, { cache: "no-store" })
      .then((r) => r.json() as Promise<State[]>)
      .then(setStates)
      .catch((err: Error) => setError(err.message));
  }, [countryId]);

  useEffect(() => {
    if (!stateId) {
      setCities([]);
      setCityId("");
      return;
    }

    const params = new URLSearchParams({ state_id: String(stateId) });
    if (cityQuery.trim()) {
      params.set("query", cityQuery.trim());
    }

    fetch(`/api/proxy/territory/cities?${params.toString()}`, { cache: "no-store" })
      .then((r) => r.json() as Promise<City[]>)
      .then(setCities)
      .catch((err: Error) => setError(err.message));
  }, [stateId, cityQuery]);

  const selectedLocation = useMemo(() => {
    const state = states.find((item) => item.id === stateId);
    const city = cities.find((item) => item.id === cityId);
    return { state, city };
  }, [stateId, cityId, states, cities]);

  async function searchPoliticians() {
    setLoading(true);
    setSelectedProfile(null);
    try {
      const params = new URLSearchParams();
      if (name.trim()) {
        params.set("name", name.trim());
      }
      if (position) {
        params.set("position", position);
      }
      if (stateId) {
        params.set("state_id", String(stateId));
      }
      if (cityId) {
        params.set("city_id", String(cityId));
      }
      params.set("active_only", activeOnly ? "true" : "false");
      params.set("limit", "120");

      const response = await fetch(`/api/proxy/politicians?${params.toString()}`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const payload = (await response.json()) as Politician[];
      setPoliticians(payload);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function openProfile(politicianId: number) {
    setLoading(true);
    try {
      const response = await fetch(`/api/proxy/politicians/${politicianId}/profile`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const payload = (await response.json()) as PoliticianProfile;
      setSelectedProfile(payload);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <section className="panel">
        <h2 style={{ margin: 0, fontFamily: "var(--font-space)" }}>Busca Investigativa de Politicos</h2>
        <p className="section-subtitle">
          Pesquise por cargo, nome e territorio para analisar contratos, gastos e emendas com dados coletados.
        </p>

        <div className="form-grid" style={{ marginTop: 12 }}>
          <div className="field">
            <label>Pais</label>
            <select
              value={countryId}
              onChange={(event) => {
                const value = event.target.value ? Number(event.target.value) : "";
                setCountryId(value);
                setStateId("");
                setCityId("");
              }}
            >
              <option value="">Selecione</option>
              {countries.map((country) => (
                <option key={country.id} value={country.id}>
                  {country.name}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Estado</label>
            <select
              value={stateId}
              disabled={!countryId}
              onChange={(event) => {
                setStateId(event.target.value ? Number(event.target.value) : "");
                setCityId("");
              }}
            >
              <option value="">Todos</option>
              {states.map((state) => (
                <option key={state.id} value={state.id}>
                  {state.name}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Buscar cidade</label>
            <input
              value={cityQuery}
              onChange={(event) => setCityQuery(event.target.value)}
              placeholder="Digite o nome da cidade"
              disabled={!stateId}
            />
          </div>

          <div className="field">
            <label>Cidade</label>
            <select
              value={cityId}
              disabled={!stateId}
              onChange={(event) => setCityId(event.target.value ? Number(event.target.value) : "")}
            >
              <option value="">Todas</option>
              {cities.map((city) => (
                <option key={city.id} value={city.id}>
                  {city.name}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Cargo politico</label>
            <select value={position} onChange={(event) => setPosition(event.target.value)}>
              <option value="">Todos</option>
              {positions.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Nome</label>
            <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Ex: Carlos" />
          </div>

          <div className="field" style={{ display: "flex", alignItems: "flex-end", gap: 8 }}>
            <input
              id="active-only"
              type="checkbox"
              checked={activeOnly}
              onChange={(event) => setActiveOnly(event.target.checked)}
              style={{ width: 18, height: 18 }}
            />
            <label htmlFor="active-only" style={{ margin: 0 }}>
              Somente mandatos ativos
            </label>
          </div>
        </div>

        <div style={{ marginTop: 12, display: "flex", gap: 10, alignItems: "center" }}>
          <button className="btn" onClick={searchPoliticians}>
            Buscar politicos
          </button>
          <p className="muted" style={{ margin: 0 }}>
            Filtro atual: {selectedLocation.state?.code || "todos estados"}
            {selectedLocation.city ? ` / ${selectedLocation.city.name}` : ""}
          </p>
        </div>
      </section>

      {error ? <div className="panel error">{error}</div> : null}

      <section className="grid-2" style={{ marginTop: 16 }}>
        <article className="panel">
          <h3 className="section-title">Resultados ({politicians.length})</h3>
          {loading ? <p className="muted">Carregando...</p> : null}
          <div className="card-list" style={{ marginTop: 8 }}>
            {politicians.map((item) => (
              <article className="card-item" key={item.id}>
                <strong>{item.name}</strong>
                <p className="muted" style={{ margin: "6px 0" }}>
                  {item.position} · {item.party || "sem partido"}
                </p>
                <button className="btn secondary" onClick={() => openProfile(item.id)}>
                  Ver dados reais
                </button>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <h3 className="section-title">Perfil investigativo</h3>
          {!selectedProfile ? (
            <p className="muted">Selecione um politico para abrir contratos, gastos e emendas.</p>
          ) : (
            <div>
              <h4 style={{ marginTop: 4 }}>{selectedProfile.politician.name}</h4>
              <p className="muted" style={{ marginTop: 4 }}>
                {selectedProfile.politician.position} · {selectedProfile.politician.party || "sem partido"}
              </p>
              <p className="muted" style={{ marginTop: 4 }}>
                Escopo: {selectedProfile.city?.name || selectedProfile.state?.name || "nacional"}
              </p>

              <div className="grid-3" style={{ marginTop: 10 }}>
                <article className="metric">
                  <p className="muted">Contratos (escopo)</p>
                  <strong>{money(selectedProfile.totals.contracts)}</strong>
                </article>
                <article className="metric">
                  <p className="muted">Gastos (escopo)</p>
                  <strong>{money(selectedProfile.totals.spending)}</strong>
                </article>
                <article className="metric">
                  <p className="muted">Emendas</p>
                  <strong>{money(selectedProfile.totals.amendments)}</strong>
                </article>
              </div>

              <h4 style={{ marginTop: 14 }}>Emendas parlamentares</h4>
              <div className="card-list">
                {selectedProfile.amendments.slice(0, 20).map((row) => (
                  <article className="card-item" key={row.id}>
                    <strong>{row.year}</strong>
                    <p className="muted" style={{ margin: "6px 0" }}>{money(row.value)}</p>
                    <p style={{ margin: 0 }}>{row.description || "Sem descricao"}</p>
                  </article>
                ))}
                {selectedProfile.amendments.length === 0 ? <p className="muted">Sem emendas para o politico.</p> : null}
              </div>
            </div>
          )}
        </article>
      </section>

      {selectedProfile ? (
        <section className="grid-2" style={{ marginTop: 16 }}>
          <article className="panel">
            <h3 className="section-title">Contratos relacionados ({selectedProfile.contracts.length})</h3>
            <div className="table-wrap" style={{ maxHeight: 360 }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Fornecedor</th>
                    <th>Valor</th>
                    <th>Inicio</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedProfile.contracts.slice(0, 40).map((row) => (
                    <tr key={row.id}>
                      <td>{row.supplier}</td>
                      <td>{money(row.value)}</td>
                      <td>{row.start_date || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>

          <article className="panel">
            <h3 className="section-title">Gastos relacionados ({selectedProfile.spending.length})</h3>
            <div className="table-wrap" style={{ maxHeight: 360 }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Ano</th>
                    <th>Mes</th>
                    <th>Categoria</th>
                    <th>Valor</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedProfile.spending.slice(0, 40).map((row) => (
                    <tr key={row.id}>
                      <td>{row.year}</td>
                      <td>{row.month}</td>
                      <td>{row.category}</td>
                      <td>{money(row.value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>
        </section>
      ) : null}
    </div>
  );
}
