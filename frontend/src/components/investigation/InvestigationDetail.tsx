"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Investigation } from "@/lib/types";

type InvestigationEntity = { id: number; investigation_id: number; entity_type: string; entity_id: number; note: string | null };
type InvestigationNote = { id: number; investigation_id: number; body: string; created_at: string };

type AnalysisResponse = { provider: string; model_id: string; answer: string };

export function InvestigationDetail({ investigationId }: { investigationId: number }) {
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [entities, setEntities] = useState<InvestigationEntity[]>([]);
  const [notes, setNotes] = useState<InvestigationNote[]>([]);
  const [entityType, setEntityType] = useState("public_agency");
  const [entityId, setEntityId] = useState("");
  const [entityNote, setEntityNote] = useState("");
  const [noteText, setNoteText] = useState("");
  const [question, setQuestion] = useState("Quais padrões suspeitos você identifica?");
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    try {
      const [item, itemEntities, itemNotes] = await Promise.all([
        api.get<Investigation>(`investigations/${investigationId}`),
        api.get<InvestigationEntity[]>(`investigations/${investigationId}/entities`),
        api.get<InvestigationNote[]>(`investigations/${investigationId}/notes`)
      ]);
      setInvestigation(item);
      setEntities(itemEntities);
      setNotes(itemNotes);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    void load();
  }, [investigationId]);

  async function addEntity() {
    if (!entityId) {
      setError("Informe o ID da entidade.");
      return;
    }
    try {
      await api.post(`investigations/${investigationId}/entities`, {
        entity_type: entityType,
        entity_id: Number(entityId),
        note: entityNote || null
      });
      setEntityId("");
      setEntityNote("");
      setMessage("Entidade adicionada à investigação.");
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function addNote() {
    if (!noteText.trim()) {
      setError("Escreva uma anotação.");
      return;
    }
    try {
      await api.post(`investigations/${investigationId}/notes`, { body: noteText });
      setNoteText("");
      setMessage("Anotação registrada.");
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function runAnalysis() {
    if (!investigation?.scope_city_id) {
      setError("Esta investigação não possui cidade de escopo para análise IA.");
      return;
    }
    try {
      const result = await api.post<AnalysisResponse>(`analysis/cities/${investigation.scope_city_id}`, {
        question
      });
      setAnalysis(result);
      setMessage(`Análise executada via ${result.provider}/${result.model_id}`);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  if (!investigation) {
    return <div className="panel">Carregando investigação...</div>;
  }

  return (
    <div>
      <section className="panel">
        <p className="brand-kicker">Investigação #{investigation.id}</p>
        <h2 style={{ margin: "8px 0" }}>{investigation.title}</h2>
        <p className="section-subtitle">{investigation.summary || "Sem resumo"}</p>
      </section>

      {error ? <div className="panel error">{error}</div> : null}
      {message ? <div className="panel success">{message}</div> : null}

      <section className="grid-2" style={{ marginTop: 16 }}>
        <article className="panel">
          <h3 className="section-title">Entidades da investigação</h3>
          <div className="form-grid" style={{ marginTop: 8 }}>
            <div className="field">
              <label>Tipo</label>
              <select value={entityType} onChange={(event) => setEntityType(event.target.value)}>
                <option value="public_agency">Órgão público</option>
                <option value="politician">Político</option>
                <option value="contract">Contrato</option>
                <option value="supplier">Fornecedor</option>
              </select>
            </div>
            <div className="field">
              <label>ID entidade</label>
              <input value={entityId} onChange={(event) => setEntityId(event.target.value)} />
            </div>
            <div className="field" style={{ gridColumn: "span 2" }}>
              <label>Nota</label>
              <input value={entityNote} onChange={(event) => setEntityNote(event.target.value)} />
            </div>
          </div>
          <button className="btn" style={{ marginTop: 10 }} onClick={addEntity}>
            Adicionar entidade
          </button>

          <div className="card-list" style={{ marginTop: 12 }}>
            {entities.map((item) => (
              <article className="card-item" key={item.id}>
                <strong>{item.entity_type}</strong> · ID {item.entity_id}
                <p className="muted" style={{ margin: "6px 0 0" }}>
                  {item.note || "Sem observação"}
                </p>
              </article>
            ))}
          </div>
        </article>

        <article className="panel">
          <h3 className="section-title">Anotações</h3>
          <div className="field" style={{ marginTop: 8 }}>
            <label>Nova anotação</label>
            <textarea value={noteText} onChange={(event) => setNoteText(event.target.value)} />
          </div>
          <button className="btn" style={{ marginTop: 10 }} onClick={addNote}>
            Salvar anotação
          </button>

          <div className="card-list" style={{ marginTop: 12 }}>
            {notes.map((note) => (
              <article className="card-item" key={note.id}>
                <p style={{ margin: 0 }}>{note.body}</p>
                <p className="muted" style={{ margin: "6px 0 0" }}>
                  {new Date(note.created_at).toLocaleString("pt-BR")}
                </p>
              </article>
            ))}
          </div>
        </article>
      </section>

      <section className="panel" style={{ marginTop: 16 }}>
        <h3 className="section-title">Análise IA da investigação</h3>
        <div className="field" style={{ marginTop: 8 }}>
          <label>Pergunta investigativa</label>
          <textarea value={question} onChange={(event) => setQuestion(event.target.value)} />
        </div>
        <button className="btn" style={{ marginTop: 10 }} onClick={runAnalysis}>
          Executar análise
        </button>
        {analysis ? (
          <article className="card-item" style={{ marginTop: 12 }}>
            <strong>
              Motor: {analysis.provider}/{analysis.model_id}
            </strong>
            <p style={{ whiteSpace: "pre-wrap" }}>{analysis.answer}</p>
          </article>
        ) : null}
      </section>
    </div>
  );
}

