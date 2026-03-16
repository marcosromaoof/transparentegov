from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.db.session import session_scope
from app.models import (
    AIProviderConfig,
    AISystemSetting,
    City,
    Contract,
    Country,
    DatasetSource,
    Hospital,
    MunicipalRevenue,
    ParliamentaryAmendment,
    PoliceUnit,
    Politician,
    PublicAgency,
    PublicServant,
    PublicSpending,
    School,
    State,
)


DATASET_DEFAULTS = [
    (
        "portal_transparencia",
        "Portal da Transparencia",
        "https://portaldatransparencia.gov.br",
        "daily",
    ),
    ("tse", "Tribunal Superior Eleitoral", "https://dadosabertos.tse.jus.br", "weekly"),
    ("camara", "Camara dos Deputados", "https://dadosabertos.camara.leg.br/api/v2", "daily"),
    ("senado", "Senado Federal", "https://legis.senado.leg.br/dadosabertos", "daily"),
    (
        "ibge",
        "Instituto Brasileiro de Geografia e Estatistica",
        "https://servicodados.ibge.gov.br/api/v1",
        "weekly",
    ),
    ("pncp", "Portal Nacional de Contratacoes Publicas", "https://pncp.gov.br/api", "daily"),
    ("base_dos_dados", "Base dos Dados", "https://basedosdados.org", "weekly"),
]


def seed_data() -> None:
    with session_scope() as db:
        brazil = db.scalar(select(Country).where(Country.code == "BR"))
        if not brazil:
            brazil = Country(name="Brasil", code="BR")
            db.add(brazil)
            db.flush()

        df = db.scalar(select(State).where(State.code == "DF", State.country_id == brazil.id))
        if not df:
            df = State(country_id=brazil.id, name="Distrito Federal", code="DF")
            db.add(df)
            db.flush()

        sp = db.scalar(select(State).where(State.code == "SP", State.country_id == brazil.id))
        if not sp:
            sp = State(country_id=brazil.id, name="Sao Paulo", code="SP")
            db.add(sp)
            db.flush()

        brasilia = db.scalar(select(City).where(City.state_id == df.id, City.name == "Brasilia"))
        if not brasilia:
            brasilia = City(
                state_id=df.id,
                name="Brasilia",
                ibge_code="5300108",
                population=2817381,
                latitude=-15.793889,
                longitude=-47.882778,
            )
            db.add(brasilia)
            db.flush()

        secretaria_saude = db.scalar(
            select(PublicAgency).where(
                PublicAgency.city_id == brasilia.id,
                PublicAgency.name == "Secretaria de Saude do DF",
            )
        )
        if not secretaria_saude:
            secretaria_saude = PublicAgency(
                city_id=brasilia.id,
                name="Secretaria de Saude do DF",
                type="secretariat",
                address="SAM Bloco A, Asa Norte",
                latitude=-15.785273,
                longitude=-47.888664,
            )
            db.add(secretaria_saude)
            db.flush()

        hospital_base = db.scalar(select(Hospital).where(Hospital.city_id == brasilia.id))
        if not hospital_base:
            db.add(
                Hospital(
                    city_id=brasilia.id,
                    name="Hospital Regional de Brasilia",
                    address="Asa Norte",
                    beds=420,
                    public=True,
                )
            )

        school_base = db.scalar(select(School).where(School.city_id == brasilia.id))
        if not school_base:
            db.add(
                School(
                    city_id=brasilia.id,
                    name="Escola Classe Modelo",
                    type="publica",
                    address="Asa Sul",
                )
            )

        police_base = db.scalar(select(PoliceUnit).where(PoliceUnit.city_id == brasilia.id))
        if not police_base:
            db.add(
                PoliceUnit(
                    city_id=brasilia.id,
                    name="5a Delegacia de Policia",
                    address="Area Central",
                    type="police_station",
                )
            )

        politician = db.scalar(select(Politician).where(Politician.name == "Politico Exemplo DF"))
        if not politician:
            politician = Politician(
                name="Politico Exemplo DF",
                party="XYZ",
                position="Deputado Distrital",
                city_id=brasilia.id,
                state_id=df.id,
                start_term=date(2023, 1, 1),
                end_term=date(2026, 12, 31),
            )
            db.add(politician)
            db.flush()

        servant = db.scalar(select(PublicServant).where(PublicServant.agency_id == secretaria_saude.id))
        if not servant:
            db.add(
                PublicServant(
                    name="Servidor Exemplo",
                    position="Analista de Gestao",
                    agency_id=secretaria_saude.id,
                    salary=Decimal("12850.00"),
                )
            )

        contract = db.scalar(select(Contract).where(Contract.agency_id == secretaria_saude.id))
        if not contract:
            db.add(
                Contract(
                    agency_id=secretaria_saude.id,
                    supplier="MedSupply Brasil LTDA",
                    value=Decimal("2450000.00"),
                    start_date=date(2025, 2, 1),
                    end_date=date(2026, 2, 1),
                    description="Contrato de insumos hospitalares",
                )
            )

        spending = db.scalar(select(PublicSpending).where(PublicSpending.agency_id == secretaria_saude.id))
        if not spending:
            db.add(
                PublicSpending(
                    agency_id=secretaria_saude.id,
                    year=2026,
                    month=1,
                    category="Saude",
                    value=Decimal("38200000.00"),
                )
            )

        amendment = db.scalar(
            select(ParliamentaryAmendment).where(ParliamentaryAmendment.city_id == brasilia.id)
        )
        if not amendment and politician:
            db.add(
                ParliamentaryAmendment(
                    politician_id=politician.id,
                    city_id=brasilia.id,
                    value=Decimal("3000000.00"),
                    year=2025,
                    description="Emenda para modernizacao da rede de saude",
                )
            )

        revenue = db.scalar(select(MunicipalRevenue).where(MunicipalRevenue.city_id == brasilia.id))
        if not revenue:
            db.add(
                MunicipalRevenue(
                    city_id=brasilia.id,
                    year=2025,
                    source="federal_transfer",
                    value=Decimal("820000000.00"),
                )
            )

        for source_key, name, endpoint_url, frequency in DATASET_DEFAULTS:
            exists = db.scalar(select(DatasetSource).where(DatasetSource.source_key == source_key))
            if not exists:
                db.add(
                    DatasetSource(
                        source_key=source_key,
                        name=name,
                        endpoint_url=endpoint_url,
                        frequency=frequency,
                        enabled=True,
                    )
                )

        for provider in ["deepseek", "google", "openai", "openrouter", "groq"]:
            exists = db.scalar(select(AIProviderConfig).where(AIProviderConfig.provider == provider))
            if not exists:
                db.add(AIProviderConfig(provider=provider, enabled=False))

        setting = db.get(AISystemSetting, 1)
        if not setting:
            db.add(AISystemSetting(id=1, selected_provider=None, selected_model_id=None))


if __name__ == "__main__":
    seed_data()
    print("Seed executado com sucesso")

