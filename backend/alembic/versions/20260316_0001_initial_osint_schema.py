"""initial osint schema

Revision ID: 20260316_0001
Revises: 
Create Date: 2026-03-16 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260316_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("api_key_hash", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "countries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=8), nullable=False, unique=True),
    )

    op.create_table(
        "states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("country_id", sa.Integer(), sa.ForeignKey("countries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=8), nullable=False),
        sa.UniqueConstraint("country_id", "code", name="uq_state_country_code"),
    )

    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("state_id", sa.Integer(), sa.ForeignKey("states.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("ibge_code", sa.String(length=16), nullable=True),
        sa.Column("population", sa.Integer(), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 6), nullable=True),
        sa.UniqueConstraint("state_id", "name", name="uq_city_state_name"),
        sa.UniqueConstraint("ibge_code", name="uq_city_ibge"),
    )

    op.create_table(
        "public_agencies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("city_id", sa.Integer(), sa.ForeignKey("cities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 6), nullable=True),
    )
    op.create_index("ix_public_agencies_city_type", "public_agencies", ["city_id", "type"])

    op.create_table(
        "hospitals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("city_id", sa.Integer(), sa.ForeignKey("cities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("beds", sa.Integer(), nullable=True),
        sa.Column("public", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "schools",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("city_id", sa.Integer(), sa.ForeignKey("cities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
    )

    op.create_table(
        "police_units",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("city_id", sa.Integer(), sa.ForeignKey("cities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("type", sa.String(length=64), nullable=False),
    )

    op.create_table(
        "politicians",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("party", sa.String(length=32), nullable=True),
        sa.Column("position", sa.String(length=128), nullable=False),
        sa.Column("city_id", sa.Integer(), sa.ForeignKey("cities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("state_id", sa.Integer(), sa.ForeignKey("states.id", ondelete="SET NULL"), nullable=True),
        sa.Column("start_term", sa.Date(), nullable=True),
        sa.Column("end_term", sa.Date(), nullable=True),
    )

    op.create_table(
        "public_servants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("position", sa.String(length=128), nullable=False),
        sa.Column("agency_id", sa.Integer(), sa.ForeignKey("public_agencies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("salary", sa.Numeric(14, 2), nullable=True),
    )

    op.create_table(
        "contracts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agency_id", sa.Integer(), sa.ForeignKey("public_agencies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Numeric(16, 2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
    )

    op.create_table(
        "public_spending",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agency_id", sa.Integer(), sa.ForeignKey("public_agencies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Numeric(16, 2), nullable=False),
    )
    op.create_index("ix_spending_agency_year_month", "public_spending", ["agency_id", "year", "month"])

    op.create_table(
        "parliamentary_amendments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("politician_id", sa.Integer(), sa.ForeignKey("politicians.id", ondelete="SET NULL"), nullable=True),
        sa.Column("city_id", sa.Integer(), sa.ForeignKey("cities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value", sa.Numeric(16, 2), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )

    op.create_table(
        "municipal_revenue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("city_id", sa.Integer(), sa.ForeignKey("cities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Numeric(16, 2), nullable=False),
    )

    op.create_table(
        "investigations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("scope_country_id", sa.Integer(), sa.ForeignKey("countries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scope_state_id", sa.Integer(), sa.ForeignKey("states.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scope_city_id", sa.Integer(), sa.ForeignKey("cities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "investigation_entities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("investigation_id", sa.Integer(), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
    )

    op.create_table(
        "investigation_notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("investigation_id", sa.Integer(), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "ai_provider_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(length=32), nullable=False, unique=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "ai_models",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("provider", "model_id", name="uq_ai_provider_model"),
    )

    op.create_table(
        "ai_system_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("selected_provider", sa.String(length=32), nullable=True),
        sa.Column("selected_model_id", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "dataset_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_key", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("endpoint_url", sa.String(length=512), nullable=False),
        sa.Column("frequency", sa.String(length=32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(length=32), nullable=True),
    )

    op.create_table(
        "collector_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_source_id", sa.Integer(), sa.ForeignKey("dataset_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_fetched", sa.Integer(), nullable=False),
        sa.Column("records_saved", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource", sa.String(length=128), nullable=False),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("collector_runs")
    op.drop_table("dataset_sources")
    op.drop_table("ai_system_settings")
    op.drop_table("ai_models")
    op.drop_table("ai_provider_configs")
    op.drop_table("investigation_notes")
    op.drop_table("investigation_entities")
    op.drop_table("investigations")
    op.drop_table("municipal_revenue")
    op.drop_table("parliamentary_amendments")
    op.drop_index("ix_spending_agency_year_month", table_name="public_spending")
    op.drop_table("public_spending")
    op.drop_table("contracts")
    op.drop_table("public_servants")
    op.drop_table("politicians")
    op.drop_table("police_units")
    op.drop_table("schools")
    op.drop_table("hospitals")
    op.drop_index("ix_public_agencies_city_type", table_name="public_agencies")
    op.drop_table("public_agencies")
    op.drop_table("cities")
    op.drop_table("states")
    op.drop_table("countries")
    op.drop_table("users")

