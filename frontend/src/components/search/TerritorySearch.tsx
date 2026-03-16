"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import type { City, Country, State } from "@/lib/types";

export function TerritorySearch() {
  const router = useRouter();

  const [countries, setCountries] = useState<Country[]>([]);
  const [states, setStates] = useState<State[]>([]);
  const [cities, setCities] = useState<City[]>([]);

  const [countryId, setCountryId] = useState<number | "">("");
  const [stateId, setStateId] = useState<number | "">("");
  const [cityId, setCityId] = useState<number | "">("");
  const [query, setQuery] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<Country[]>("territory/countries").then(setCountries).catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!countryId) {
      setStates([]);
      return;
    }
    api.get<State[]>(`territory/states?country_id=${countryId}`)
      .then(setStates)
      .catch((err: Error) => setError(err.message));
  }, [countryId]);

  useEffect(() => {
    if (!stateId) {
      setCities([]);
      return;
    }

    const params = new URLSearchParams({ state_id: String(stateId) });
    if (query.trim()) {
      params.set("query", query.trim());
    }

    setLoading(true);
    api.get<City[]>(`territory/cities?${params.toString()}`)
      .then(setCities)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [stateId, query]);

  const selectedCity = useMemo(() => cities.find((c) => c.id === cityId), [cities, cityId]);

  return (
    <div className="panel">
      <div className="hero">
        <p className="brand-kicker">Fluxo Investigativo</p>
        <h2>Busca Territorial OSINT</h2>
        <p>
          Selecione país, estado e cidade para carregar o perfil investigativo completo com órgãos públicos,
          contratos, gastos, emendas e rede de relações.
        </p>
      </div>

      <div className="form-grid">
        <div className="field">
          <label>País</label>
          <select
            value={countryId}
            onChange={(event) => {
              setCountryId(event.target.value ? Number(event.target.value) : "");
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
            onChange={(event) => {
              setStateId(event.target.value ? Number(event.target.value) : "");
              setCityId("");
            }}
            disabled={!countryId}
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
          <label>Busca por cidade</label>
          <input
            placeholder="Digite parte do nome da cidade"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            disabled={!stateId}
          />
        </div>

        <div className="field">
          <label>Cidade</label>
          <select
            value={cityId}
            onChange={(event) => setCityId(event.target.value ? Number(event.target.value) : "")}
            disabled={!stateId || loading}
          >
            <option value="">Selecione</option>
            {cities.map((city) => (
              <option key={city.id} value={city.id}>
                {city.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div style={{ marginTop: 14, display: "flex", alignItems: "center", gap: 12 }}>
        <button className="btn" onClick={() => cityId && router.push(`/city/${cityId}`)} disabled={!cityId}>
          Investigar território
        </button>
        {selectedCity ? <p className="muted">Cidade selecionada: {selectedCity.name}</p> : null}
      </div>

      {error ? (
        <motion.p className="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ marginTop: 12 }}>
          {error}
        </motion.p>
      ) : null}
    </div>
  );
}

