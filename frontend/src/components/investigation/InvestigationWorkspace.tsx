"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { City, Country, Investigation, State } from "@/lib/types";

export function InvestigationWorkspace() {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [countries, setCountries] = useState<Country[]>([]);
  const [states, setStates] = useState<State[]>([]);
  const [cities, setCities] = useState<City[]>([]);

  const [countryId, setCountryId] = useState<number | "">("");
  const [stateId, setStateId] = useState<number | "">("");
  const [cityId, setCityId] = useState<number | "">("");
  const [cityQuery, setCityQuery] = useState("");

  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadInvestigations() {
    try {
      const rows = await api.get<Investigation[]>("investigations");
      setInvestigations(rows);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    api.get<Country[]>("territory/countries")
      .then((rows) => {
        setCountries(rows);
        if (rows.length === 1) {
          setCountryId(rows[0].id);
        }
      })
      .catch((err: Error) => setError(err.message));

    void loadInvestigations();
  }, []);

  useEffect(() => {
    if (!countryId) {
      setStates([]);
      setStateId("");
      setCities([]);
      setCityId("");
      return;
    }

    api.get<State[]>(`territory/states?country_id=${countryId}`)
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

    api.get<City[]>(`territory/cities?${params.toString()}`)
      .then(setCities)
      .catch((err: Error) => setError(err.message));
  }, [stateId, cityQuery]);

  async function createInvestigation() {
    if (title.trim().length < 4) {
      setError("Titulo deve ter pelo menos 4 caracteres.");
      return;
    }

    try {
      await api.post("investigations", {
        title: title.trim(),
        summary: summary.trim() || null,
        scope_city_id: cityId || null,
      });
      setTitle("");
      setSummary("");
      setCityId("");
      setCityQuery("");
      setMessage("Investigacao criada com sucesso.");
      await loadInvestigations();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div>
      <section className="panel">
        <h2 style={{ margin: 0, fontFamily: "var(--font-space)" }}>Workspace Investigativo</h2>
        <p className="section-subtitle">Monte casos com escopo territorial e entidades relevantes.</p>

        <div className="form-grid" style={{ marginTop: 12 }}>
          <div className="field" style={{ gridColumn: "span 2" }}>
            <label>Titulo da investigacao</label>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Ex: Gastos da saude em Brasilia"
            />
          </div>

          <div className="field">
            <label>Pais</label>
            <select
              value={countryId}
              onChange={(event) => {
                const value = event.target.value ? Number(event.target.value) : "";
                setCountryId(value);
                setStateId("");
                setCityId("");
                setCities([]);
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
              <option value="">Selecione</option>
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
            <label>Cidade (escopo)</label>
            <select
              value={cityId}
              disabled={!stateId}
              onChange={(event) => setCityId(event.target.value ? Number(event.target.value) : "")}
            >
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
          Criar investigacao
        </button>
      </section>

      {message ? <div className="panel success">{message}</div> : null}
      {error ? <div className="panel error">{error}</div> : null}

      <section className="panel" style={{ marginTop: 16 }}>
        <h3 className="section-title">Investigacoes cadastradas</h3>
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
                  Abrir investigacao
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
