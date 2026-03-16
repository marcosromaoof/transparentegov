# Official Data Expansion Plan

Date: 2026-03-16

## Objective

Expand the platform from a partial territorial prototype into a real OSINT system for:

- city and state public finances
- mayor, governor, senator, deputy and councilor search by name
- presidency and federal executive spending
- federal parliamentary expenses and budget amendments
- municipal and state infrastructure coverage

## Current Audit Of The Codebase

What exists today:

- `ibge`: loads country, state and city territory.
- `tse`: loads elected politicians for 2024 and 2022 from the TSE candidate files.
- `senado`: loads the current list of senators only.
- `camara`: loads current federal deputies and a limited sample of expense records.
- `portal_transparencia`: loads parliamentary amendments from the federal Portal da Transparencia.
- `pncp`: loads contracts and spending derived from PNCP contracts.

What is still missing:

- no state-level revenue or spending tables
- no state-level comparison module (`gasto vs receita`)
- no dedicated presidency spending dataset or UI
- no municipal revenue collector beyond seed/demo data
- no real ingestion from `base_dos_dados` yet
- no collector for schools from INEP microdata
- no collector for health establishments from CNES
- no unified search workspace for `Presidente`, `Governador`, `Prefeito`, `Senador`, `Deputado Federal`, `Deputado Estadual`, `Deputado Distrital`, `Vereador`
- no dedicated budget-amendment module for Câmara/Infoleg budget data

## Verified Official Sources

### Federal Executive And Presidency

- Portal da Transparencia API:
  - https://portaldatransparencia.gov.br/api-de-dados
- Portal da Transparencia data origin page:
  - https://portaldatransparencia.gov.br/origem-dos-dados
- Federal public spending and organ pages:
  - https://portaldatransparencia.gov.br/despesas
  - https://portaldatransparencia.gov.br/orgaos-superiores/20000-
- Card payment consultations relevant for presidency/executive spending:
  - https://api-d.portaldatransparencia.gov.br/cartoes/consulta

Primary data confirmed from the official pages:

- federal public spending
- executive contracts
- licitacoes
- viagens a servico
- servidores do Poder Executivo Federal
- cartoes de pagamento do Governo Federal
- organ-level budget and expense views

### State And Municipal Finances

- Siconfi API de Dados Abertos:
  - https://www.tesourotransparente.gov.br/consultas/consultas-siconfi/siconfi-api-de-dados-abertos
- FINBRA municipal finance page:
  - https://www.gov.br/tesouronacional/pt-br/estados-e-municipios/dados-consolidados/finbra-financas-municipais
- FINBRA consultation manual:
  - https://manualsiconfi.tesouro.gov.br/area-publica/consultas/consultar-finbra/consultar-dados-finbra
- Siconfi fiscal indicators map:
  - https://www.tesourotransparente.gov.br/consultas/consultas-siconfi/siconfi-indicadores-fiscais-mapa

Primary data confirmed from the official pages:

- states, DF and municipalities
- FINBRA annual accounts
- RREO and RGF fiscal reports
- revenue, expenditure, debt, personnel and fiscal indicators
- paginated JSON API with up to 5,000 items per page

### Legislative Data

- Câmara Dados Abertos Swagger:
  - https://dadosabertos.camara.leg.br/swagger/api.html
- Câmara paginated API guidance:
  - https://dadosabertos.camara.leg.br/howtouse/2017-05-16-js-resultados-paginados.html
- Infoleg Orcamento:
  - https://www2.camara.leg.br/infoleg/aplicativo/orcamento
- Senado current senators endpoint:
  - https://legis.senado.leg.br/dadosabertos/senador/lista/atual.json

Primary data confirmed from the official pages:

- full deputy list
- deputy expenses (Cota para Exercício da Atividade Parlamentar)
- legislative organs, memberships, propositions and votes
- Senate current senator roster
- budget/emenda execution visibility via Infoleg Orcamento

Important note:

- I verified official Câmara open-data coverage for deputies, expenses, organs, propositions and votes.
- I verified official Senate roster access.
- I did not confirm, from primary Senate documentation in this audit, a stable official endpoint for senator expense extraction equivalent to the Câmara expense endpoint. This should be treated as a separate discovery task before implementation.

### Elections, Cities, Health And Education

- TSE candidate and election open data:
  - https://dadosabertos.tse.jus.br
- INEP Censo Escolar microdata:
  - https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar
- CNES open dataset:
  - https://dadosabertos.saude.gov.br/dataset/cnes-cadastro-nacional-de-estabelecimentos-de-saude

Primary data confirmed from the official pages:

- elected politicians and candidates by cargo and municipality
- school microdata by municipality
- health establishments by municipality

Important note:

- I did not confirm a single, unified national official dataset for police stations, battalions and fire departments in the same way that CNES and INEP cover health and education.
- For public security infrastructure, the platform should be designed for state-specific collectors.

## Recommended Data Model Expansion

Add these tables before new collectors:

- `state_revenue`
- `state_spending`
- `state_investment`
- `fiscal_indicator_snapshots`
- `federal_executive_spending`
- `presidential_card_expenses`
- `parliamentary_quota_expenses`
- `chamber_budget_amendments`
- `school_units`
- `health_units`
- `state_security_units`
- `dataset_coverage_snapshots`

Extend these existing tables:

- `politicians`
  - add `source_system`
  - add `source_person_id`
  - add `office_scope`
  - add `is_current`
- `public_agencies`
  - add `source_system`
  - add `source_external_id`
  - add `managing_level`

## Search And Navigation Redesign

The search system should be reorganized into a single investigative search layer:

- search by person name
- search by political name
- search by cargo
- search by city
- search by state
- search by agency
- search by supplier

Required filters:

- `cargo`
- `nome`
- `estado`
- `cidade`
- `mandato_atual`
- `fonte`
- `ano`

Required role taxonomy:

- Presidente
- Governador
- Prefeito
- Senador
- Deputado Federal
- Deputado Estadual
- Deputado Distrital
- Vereador

## Implementation Phases

### Phase 1 - Scope Correction And Search Foundation

- fix city profile to count only municipal politicians
- expose a role taxonomy endpoint with normalized cargos
- support search by `name + cargo + state + city` across all politicians
- add result grouping by `federal`, `state`, `municipal`
- add coverage badges to cities so the UI can distinguish `city with financial data` from `city without collected financial data`

### Phase 2 - State And Municipal Finances

- implement `siconfi_finbra` collector
- ingest annual and periodic revenue/spending for states and municipalities
- create state profile page with:
  - receita total
  - gasto total
  - investimento
  - divida
  - indicadores fiscais
- create `estado vs municipios` comparison views

### Phase 3 - Presidency And Federal Executive Spending

- implement collectors for:
  - public spending by organ
  - executive contracts
  - card payments
  - travel spending
- add `Presidencia` page and `gastos do presidente` tab
- add executive-organ investigative pages with supplier, category and time breakdown

### Phase 4 - Câmara And Budget Intelligence

- expand `camara` collector to ingest:
  - complete deputy roster
  - full CEAP expenses by year
  - organs and memberships
  - propositions and votes
- create `deputado federal` profile by name, not only by source id
- integrate budget-amendment intelligence using Câmara open data plus Infoleg Orcamento for execution tracking

### Phase 5 - Municipal Infrastructure

- implement `cnes` collector for hospitals and health units
- implement `inep_censo_escolar` collector for schools
- design a pluggable collector interface for state security datasets
- enrich city profile with real facility coverage instead of derived guesses only

### Phase 6 - Investigative Workspace

- add dedicated tabs:
  - `Presidencia`
  - `Estados`
  - `Municipios`
  - `Deputados`
  - `Senadores`
  - `Prefeitos`
  - `Vereadores`
  - `Emendas`
  - `Receita vs Gasto`
- add saved comparative investigations:
  - `Estado vs receita`
  - `Cidade vs fornecedores`
  - `Politico vs emendas`
  - `Presidencia vs cartoes`

## Priority Order

1. `siconfi_finbra` collector and state/municipal finance schema
2. presidency and federal executive spending collector set
3. expanded Câmara collector for deputy search by name and full expense history
4. CNES and INEP collectors for municipal infrastructure
5. state-specific security collectors

## Immediate Next Build Target

The next concrete delivery should be:

- `state_revenue`, `state_spending`, `state_investment` schema
- `siconfi_finbra` collector
- state profile UI with `receita vs gasto`
- municipal coverage index in the city search UI
- unified politician search with normalized cargos

This is the minimum step that removes the current architectural bottleneck: the platform still lacks a real state/municipal fiscal backbone.
