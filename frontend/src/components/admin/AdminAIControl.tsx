"use client";

import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import type { ModelSelection, ProviderConfig, ProviderModel } from "@/lib/types";

const PROVIDERS: ProviderConfig["provider"][] = ["deepseek", "google", "openai", "openrouter", "groq"];

export function AdminAIControl() {
  const [providers, setProviders] = useState<ProviderConfig[]>([]);
  const [models, setModels] = useState<Record<string, ProviderModel[]>>({});
  const [selection, setSelection] = useState<ModelSelection>({ provider: null, model_id: null });
  const [keys, setKeys] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [providersResponse, selectionResponse] = await Promise.all([
        api.get<ProviderConfig[]>("admin/providers"),
        api.get<ModelSelection>("admin/model-selection")
      ]);

      setProviders(providersResponse);
      setSelection(selectionResponse);

      for (const provider of PROVIDERS) {
        const providerModels = await api.get<ProviderModel[]>(`admin/providers/${provider}/models`);
        setModels((prev) => ({ ...prev, [provider]: providerModels }));
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function saveKey(provider: string) {
    const apiKey = keys[provider]?.trim();
    if (!apiKey) {
      setError(`Informe a chave API para ${provider}`);
      return;
    }

    setError(null);
    setMessage(null);
    try {
      await api.put(`admin/providers/${provider}`, { api_key: apiKey, enabled: true });
      setMessage(`Chave de ${provider} salva com sucesso.`);
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function syncModels(provider: string) {
    setError(null);
    setMessage(null);
    try {
      const synced = await api.post<ProviderModel[]>(`admin/providers/${provider}/sync-models`);
      setModels((prev) => ({ ...prev, [provider]: synced }));
      setMessage(`${synced.length} modelos sincronizados em ${provider}.`);
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function saveSelection() {
    if (!selection.provider || !selection.model_id) {
      setError("Selecione provedor e modelo antes de salvar.");
      return;
    }
    setError(null);
    setMessage(null);

    try {
      const result = await api.put<ModelSelection>("admin/model-selection", {
        provider: selection.provider,
        model_id: selection.model_id
      });
      setSelection(result);
      setMessage(`Modelo ativo configurado: ${result.provider}/${result.model_id}`);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  const availableModels = useMemo(() => {
    if (!selection.provider) {
      return [];
    }
    return models[selection.provider] || [];
  }, [models, selection.provider]);

  return (
    <div>
      <section className="panel">
        <p className="brand-kicker">Painel Administrativo</p>
        <h2 style={{ margin: "6px 0 8px", fontFamily: "var(--font-space)", fontSize: "1.8rem" }}>
          Configuração de IA e Integrações
        </h2>
        <p className="section-subtitle">
          O sistema opera com apenas um modelo selecionado e persistido. Não existe fallback automático.
        </p>
      </section>

      {loading ? <div className="panel">Carregando configurações...</div> : null}
      {error ? <div className="panel error">{error}</div> : null}
      {message ? <div className="panel success">{message}</div> : null}

      <section className="grid-2" style={{ marginTop: 16 }}>
        {providers.map((provider) => (
          <article key={provider.provider} className="panel">
            <h3 className="section-title" style={{ textTransform: "capitalize" }}>
              {provider.provider}
            </h3>
            <p className="section-subtitle">
              Status: {provider.enabled ? "ativo" : "inativo"} · Chave configurada: {provider.configured ? "sim" : "não"}
            </p>
            <div className="field" style={{ marginTop: 12 }}>
              <label>Nova chave API</label>
              <input
                type="password"
                placeholder={`Cole a API key de ${provider.provider}`}
                value={keys[provider.provider] || ""}
                onChange={(event) => setKeys((prev) => ({ ...prev, [provider.provider]: event.target.value }))}
              />
            </div>

            <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
              <button className="btn" onClick={() => saveKey(provider.provider)}>
                Salvar chave
              </button>
              <button className="btn secondary" onClick={() => syncModels(provider.provider)}>
                Buscar modelos
              </button>
            </div>

            <p className="muted" style={{ marginTop: 10 }}>
              Modelos carregados: {(models[provider.provider] || []).length}
            </p>
          </article>
        ))}
      </section>

      <section className="panel" style={{ marginTop: 16 }}>
        <h3 className="section-title">Modelo Ativo do Sistema</h3>
        <p className="section-subtitle">
          Escolha manual do provedor/modelo. A troca só ocorre quando o administrador altera esta configuração.
        </p>

        <div className="form-grid" style={{ marginTop: 12 }}>
          <div className="field">
            <label>Provedor</label>
            <select
              value={selection.provider || ""}
              onChange={(event) =>
                setSelection({ provider: event.target.value || null, model_id: null })
              }
            >
              <option value="">Selecione</option>
              {providers
                .filter((provider) => provider.configured)
                .map((provider) => (
                  <option key={provider.provider} value={provider.provider}>
                    {provider.provider}
                  </option>
                ))}
            </select>
          </div>

          <div className="field" style={{ gridColumn: "span 2" }}>
            <label>Modelo</label>
            <select
              value={selection.model_id || ""}
              onChange={(event) => setSelection((prev) => ({ ...prev, model_id: event.target.value || null }))}
              disabled={!selection.provider}
            >
              <option value="">Selecione</option>
              {availableModels.map((model) => (
                <option key={model.model_id} value={model.model_id}>
                  {model.name} ({model.model_id})
                </option>
              ))}
            </select>
          </div>
        </div>

        <button className="btn" style={{ marginTop: 12 }} onClick={saveSelection}>
          Salvar modelo ativo
        </button>
      </section>
    </div>
  );
}

