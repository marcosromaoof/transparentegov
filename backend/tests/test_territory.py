from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models import City, Country, Politician, State
from app.services.territory import get_city_profile


def test_city_profile_only_returns_municipal_politicians() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    with SessionLocal() as db:
        country = Country(name="Brasil", code="BR")
        db.add(country)
        db.flush()

        state = State(country_id=country.id, name="Goias", code="GO")
        db.add(state)
        db.flush()

        city = City(state_id=state.id, name="Mutunopolis", ibge_code="5214101")
        db.add(city)
        db.flush()

        db.add(
            Politician(
                name="Prefeita Municipal",
                party="ABC",
                position="Prefeito",
                city_id=city.id,
                state_id=state.id,
            )
        )
        db.add(
            Politician(
                name="Senador Estadual",
                party="XYZ",
                position="Senador",
                city_id=None,
                state_id=state.id,
            )
        )
        db.commit()

        payload = get_city_profile(db, city.id)

    politicians = payload["politicians"]
    assert len(politicians) == 1
    assert politicians[0].name == "Prefeita Municipal"
