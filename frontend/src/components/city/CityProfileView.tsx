"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";

import { api } from "@/lib/api";
import type { CityProfile } from "@/lib/types";
import { CityMap } from "@/components/city/CityMap";
import { CityRelationsGraph } from "@/components/city/CityRelationsGraph";
import { CityTables } from "@/components/city/CityTables";

function money(value: string | number) {
  const numeric = typeof value === "string" ? Number(value) : value;
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(numeric || 0));
}

export function CityProfileView({ cityId }: { cityId: number }) {
  const [profile, setProfile] = useState<CityProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api.get<CityProfile>(`territory/cities/${cityId}/profile`)
      .then(setProfile)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [cityId]);

  const metrics = useMemo(() => {
    if (!profile) {
      return [];
    }
    return [
      { label: "Receita total", value: money(profile.totals.revenues) },
      { label: "Gasto total", value: money(profile.totals.spending) },
      { label: "Contratos", value: money(profile.totals.contracts) },
      { label: "Emendas", value: money(profile.totals.amendments) }
    ];
  }, [profile]);

  const hasCityData = useMemo(() => {
    if (!profile) {
      return false;
    }
    return (
      profile.public_agencies.length > 0 ||
      profile.contracts.length > 0 ||
      profile.spending.length > 0 ||
      profile.hospitals.length > 0 ||
      profile.schools.length > 0 ||
      profile.police_units.length > 0 ||
      Number(profile.totals.revenues) > 0 ||
      Number(profile.totals.amendments) > 0
    );
  }, [profile]);

  if (loading) {
    return <div className="panel">Carregando perfil investigativo...</div>;
  }

  if (error || !profile) {
    return <div className="panel error">{error || "Perfil nao encontrado"}</div>;
  }

  return (
    <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
      <section className="panel">
        <p className="brand-kicker">Territorio Investigado</p>
        <h2 style={{ margin: "6px 0 8px", fontFamily: "var(--font-space)", fontSize: "1.9rem" }}>
          {profile.city.name} · {profile.state.code} · {profile.country.code}
        </h2>
        <p className="section-subtitle">
          Estrutura publica territorial com foco investigativo em gastos, contratos, orgaos e relacoes.
        </p>

        <div className="grid-3" style={{ marginTop: 14 }}>
          {metrics.map((metric) => (
            <article key={metric.label} className="metric">
              <p className="muted">{metric.label}</p>
              <strong>{metric.value}</strong>
            </article>
          ))}
          <article className="metric">
            <p className="muted">Orgaos publicos</p>
            <strong>{profile.public_agencies.length}</strong>
          </article>
          <article className="metric">
            <p className="muted">Hospitais / Escolas / Policia</p>
            <strong>
              {profile.hospitals.length} / {profile.schools.length} / {profile.police_units.length}
            </strong>
          </article>
          <article className="metric">
            <p className="muted">Politicos do municipio</p>
            <strong>{profile.politicians.length}</strong>
          </article>
        </div>
      </section>

      {!hasCityData ? (
        <section className="panel warn" style={{ marginTop: 16 }}>
          <h3 className="section-title">Dados territoriais ainda em coleta</h3>
          <p className="section-subtitle">
            A cidade selecionada ainda nao possui cobertura financeira municipal suficiente no banco.
            Hoje a cobertura real depende principalmente de PNCP, Portal da Transparencia
            e das bases territoriais ja sincronizadas.
          </p>
        </section>
      ) : null}

      <section className="panel" style={{ marginTop: 16 }}>
        <h3 className="section-title">Mapa Territorial</h3>
        <p className="section-subtitle" style={{ marginBottom: 12 }}>
          Localizacao geografica da cidade e ponto central da investigacao.
        </p>
        <CityMap latitude={profile.city.latitude} longitude={profile.city.longitude} name={profile.city.name} />
      </section>

      <section style={{ marginTop: 16 }}>
        <CityTables profile={profile} />
      </section>

      <section style={{ marginTop: 16 }}>
        <CityRelationsGraph profile={profile} />
      </section>
    </motion.div>
  );
}
