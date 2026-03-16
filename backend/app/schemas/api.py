from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CountryOut(ORMModel):
    id: int
    name: str
    code: str


class StateOut(ORMModel):
    id: int
    country_id: int
    name: str
    code: str


class CityOut(ORMModel):
    id: int
    state_id: int
    name: str
    ibge_code: str | None
    population: int | None
    latitude: Decimal | None
    longitude: Decimal | None


class PublicAgencyOut(ORMModel):
    id: int
    city_id: int
    name: str
    type: str
    address: str | None
    latitude: Decimal | None
    longitude: Decimal | None


class HospitalOut(ORMModel):
    id: int
    city_id: int
    name: str
    address: str | None
    beds: int | None
    public: bool


class SchoolOut(ORMModel):
    id: int
    city_id: int
    name: str
    type: str
    address: str | None


class PoliceUnitOut(ORMModel):
    id: int
    city_id: int
    name: str
    address: str | None
    type: str


class PoliticianOut(ORMModel):
    id: int
    name: str
    party: str | None
    position: str
    city_id: int | None
    state_id: int | None
    start_term: date | None
    end_term: date | None


class PoliticianProfileOut(BaseModel):
    politician: PoliticianOut
    state: StateOut | None
    city: CityOut | None
    contracts: list[ContractOut]
    spending: list[PublicSpendingOut]
    amendments: list[ParliamentaryAmendmentOut]
    totals: dict[str, Decimal]


class PublicServantOut(ORMModel):
    id: int
    name: str
    position: str
    agency_id: int
    salary: Decimal | None


class ContractOut(ORMModel):
    id: int
    agency_id: int
    supplier: str
    value: Decimal
    start_date: date | None
    end_date: date | None
    description: str | None


class PublicSpendingOut(ORMModel):
    id: int
    agency_id: int
    year: int
    month: int
    category: str
    value: Decimal


class ParliamentaryAmendmentOut(ORMModel):
    id: int
    politician_id: int | None
    city_id: int
    value: Decimal
    year: int
    description: str | None


class MunicipalRevenueOut(ORMModel):
    id: int
    city_id: int
    year: int
    source: str
    value: Decimal


class CityProfileOut(ORMModel):
    city: CityOut
    country: CountryOut
    state: StateOut
    public_agencies: list[PublicAgencyOut]
    hospitals: list[HospitalOut]
    schools: list[SchoolOut]
    police_units: list[PoliceUnitOut]
    politicians: list[PoliticianOut]
    contracts: list[ContractOut]
    spending: list[PublicSpendingOut]
    amendments: list[ParliamentaryAmendmentOut]
    revenues: list[MunicipalRevenueOut]
    totals: dict[str, Decimal]


class InvestigationCreate(BaseModel):
    title: str = Field(min_length=4, max_length=255)
    summary: str | None = None
    scope_country_id: int | None = None
    scope_state_id: int | None = None
    scope_city_id: int | None = None


class InvestigationOut(ORMModel):
    id: int
    title: str
    status: str
    summary: str | None
    scope_country_id: int | None
    scope_state_id: int | None
    scope_city_id: int | None
    created_at: datetime
    updated_at: datetime


class InvestigationEntityCreate(BaseModel):
    entity_type: str
    entity_id: int
    note: str | None = None


class InvestigationEntityOut(ORMModel):
    id: int
    investigation_id: int
    entity_type: str
    entity_id: int
    note: str | None


class InvestigationNoteCreate(BaseModel):
    body: str = Field(min_length=1)


class InvestigationNoteOut(ORMModel):
    id: int
    investigation_id: int
    body: str
    created_at: datetime


class AIProviderOut(ORMModel):
    provider: str
    enabled: bool
    configured: bool
    last_sync_at: datetime | None


class AIProviderKeyUpdate(BaseModel):
    api_key: str
    enabled: bool = True


class AIModelOut(ORMModel):
    id: int
    provider: str
    model_id: str
    name: str
    metadata_json: dict[str, Any] | None
    is_active: bool
    synced_at: datetime


class AISelectionUpdate(BaseModel):
    provider: Literal["openai", "google", "deepseek", "openrouter", "groq"]
    model_id: str


class AISelectionOut(ORMModel):
    provider: str | None
    model_id: str | None


class DatasetSourceOut(ORMModel):
    id: int
    source_key: str
    name: str
    endpoint_url: str
    frequency: str
    enabled: bool
    last_run_at: datetime | None
    last_status: str | None


class DatasetSourceUpdate(BaseModel):
    frequency: str | None = None
    enabled: bool | None = None


class CollectorRunRequest(BaseModel):
    source_key: str


class CollectorRunOut(ORMModel):
    id: int
    dataset_source_id: int
    status: str
    started_at: datetime
    finished_at: datetime | None
    records_fetched: int
    records_saved: int
    error_message: str | None


class AnalysisRequest(BaseModel):
    question: str = Field(min_length=4)


class AnalysisResponse(BaseModel):
    provider: str
    model_id: str
    answer: str


class ReportResponse(BaseModel):
    investigation_id: int
    format: str
    content: str

