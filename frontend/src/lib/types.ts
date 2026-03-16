export type Country = { id: number; name: string; code: string };
export type State = { id: number; country_id: number; name: string; code: string };
export type City = {
  id: number;
  state_id: number;
  name: string;
  ibge_code: string | null;
  population: number | null;
  latitude: number | null;
  longitude: number | null;
};

export type PublicAgency = {
  id: number;
  city_id: number;
  name: string;
  type: string;
  address: string | null;
  latitude: number | null;
  longitude: number | null;
};

export type CityProfile = {
  city: City;
  state: State;
  country: Country;
  public_agencies: PublicAgency[];
  hospitals: { id: number; name: string; address: string | null; beds: number | null; public: boolean }[];
  schools: { id: number; name: string; type: string; address: string | null }[];
  police_units: { id: number; name: string; type: string; address: string | null }[];
  politicians: {
    id: number;
    name: string;
    party: string | null;
    position: string;
    city_id: number | null;
    state_id: number | null;
    start_term: string | null;
    end_term: string | null;
  }[];
  contracts: {
    id: number;
    agency_id: number;
    supplier: string;
    value: string;
    start_date: string | null;
    end_date: string | null;
    description: string | null;
  }[];
  spending: {
    id: number;
    agency_id: number;
    year: number;
    month: number;
    category: string;
    value: string;
  }[];
  amendments: { id: number; politician_id: number | null; city_id: number; value: string; year: number; description: string | null }[];
  revenues: { id: number; city_id: number; year: number; source: string; value: string }[];
  totals: { contracts: string; spending: string; revenues: string; amendments: string };
};

export type Investigation = {
  id: number;
  title: string;
  status: string;
  summary: string | null;
  scope_country_id: number | null;
  scope_state_id: number | null;
  scope_city_id: number | null;
  created_at: string;
  updated_at: string;
};

export type Politician = {
  id: number;
  name: string;
  party: string | null;
  position: string;
  city_id: number | null;
  state_id: number | null;
  start_term: string | null;
  end_term: string | null;
};

export type PoliticianProfile = {
  politician: Politician;
  state: State | null;
  city: City | null;
  contracts: {
    id: number;
    agency_id: number;
    supplier: string;
    value: string;
    start_date: string | null;
    end_date: string | null;
    description: string | null;
  }[];
  spending: {
    id: number;
    agency_id: number;
    year: number;
    month: number;
    category: string;
    value: string;
  }[];
  amendments: {
    id: number;
    politician_id: number | null;
    city_id: number;
    value: string;
    year: number;
    description: string | null;
  }[];
  totals: {
    contracts: string;
    spending: string;
    amendments: string;
  };
};

export type ProviderConfig = {
  provider: "deepseek" | "google" | "openai" | "openrouter" | "groq";
  enabled: boolean;
  configured: boolean;
  last_sync_at: string | null;
};

export type ProviderModel = {
  id: number;
  provider: string;
  model_id: string;
  name: string;
  metadata_json: Record<string, unknown> | null;
  is_active: boolean;
  synced_at: string;
};

export type ModelSelection = {
  provider: string | null;
  model_id: string | null;
};

export type DatasetSource = {
  id: number;
  source_key: string;
  name: string;
  endpoint_url: string;
  frequency: string;
  enabled: boolean;
  last_run_at: string | null;
  last_status: string | null;
};

export type CollectorRun = {
  id: number;
  dataset_source_id: number;
  status: string;
  started_at: string;
  finished_at: string | null;
  records_fetched: number;
  records_saved: number;
  error_message: string | null;
};

