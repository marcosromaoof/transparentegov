# OSINT_PUBLIC_INTELLIGENCE_PLATFORM_SPEC

Documento-base de reimplementação da plataforma TransparenteGov para investigação pública territorial.

## Foco

- investigação territorial (país > estado > cidade)
- exploração de estrutura pública por localidade
- análise profunda de gastos, contratos, emendas e receita
- correlação de entidades públicas e fornecedores
- relatórios investigativos com suporte de IA

## Módulos obrigatórios implementados

- Busca OSINT (home)
- Perfil investigativo da cidade
- Entidades
- Relações (grafo)
- Investigações (workspace)
- Datasets (coleta)
- Relatórios
- Admin (IA + integrações)

## IA

Provedores suportados:

- deepseek
- google
- openai
- openrouter
- groq

Regras:

- modelos apenas via sincronização real de API
- sem modelos mock
- sem fallback automático
- seleção persistente de 1 modelo ativo