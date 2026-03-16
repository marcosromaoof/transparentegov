import { TerritorySearch } from "@/components/search/TerritorySearch";

export default function HomePage() {
  return (
    <div>
      <section>
        <TerritorySearch />
      </section>

      <section className="grid-3" style={{ marginTop: 16 }}>
        <article className="panel">
          <h3 className="section-title">Exploração Investigativa</h3>
          <p className="section-subtitle">
            Navegação por cidade, órgão, contrato, político e conexões entre entidades públicas.
          </p>
        </article>

        <article className="panel">
          <h3 className="section-title">Correlações OSINT</h3>
          <p className="section-subtitle">
            Grafo de relações entre órgão, fornecedor, contrato e agente político com foco em hipóteses auditáveis.
          </p>
        </article>

        <article className="panel">
          <h3 className="section-title">Análise com IA</h3>
          <p className="section-subtitle">
            Modelo único configurável no Admin, sem fallback, com análise factual de gastos e contratos.
          </p>
        </article>
      </section>
    </div>
  );
}

