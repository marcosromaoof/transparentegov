from __future__ import annotations

from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.services.investigations import get_investigation
from app.services.territory import get_city_profile


def build_markdown_report(db: Session, investigation_id: int) -> str:
    investigation = get_investigation(db, investigation_id)
    lines = [
        f"# Relatorio Investigativo: {investigation.title}",
        "",
        f"Status: {investigation.status}",
        f"Atualizado em: {investigation.updated_at.isoformat()}",
        "",
    ]
    if investigation.summary:
        lines.extend(["## Resumo", investigation.summary, ""])

    if investigation.scope_city_id:
        profile = get_city_profile(db, investigation.scope_city_id)
        lines.extend(
            [
                "## Territorio Investigado",
                f"Cidade: {profile['city'].name}",
                f"Estado: {profile['state'].name}",
                "",
                "## Estrutura Administrativa",
                f"Orgaos publicos: {len(profile['public_agencies'])}",
                f"Hospitais: {len(profile['hospitals'])}",
                f"Escolas: {len(profile['schools'])}",
                f"Delegacias/unidades policiais: {len(profile['police_units'])}",
                "",
                "## Valores Consolidados",
                f"Receita total: R$ {profile['totals']['revenues']}",
                f"Gastos totais: R$ {profile['totals']['spending']}",
                f"Contratos totais: R$ {profile['totals']['contracts']}",
                f"Emendas totais: R$ {profile['totals']['amendments']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Alertas Investigativos",
            "- Verificar concentracao de fornecedores em contratos recorrentes.",
            "- Cruzar crescimento de gastos por categoria com periodo eleitoral.",
            "- Priorizar orgaos com maior relacao gasto/entrega de servico.",
            "",
            f"_Gerado automaticamente em {datetime.utcnow().isoformat()}Z_",
        ]
    )
    return "\n".join(lines)


def build_pdf_from_markdown(markdown_text: str) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50
    for line in markdown_text.splitlines():
        if y < 50:
            pdf.showPage()
            y = height - 50
        pdf.drawString(40, y, line[:120])
        y -= 16
    pdf.save()
    buffer.seek(0)
    return buffer.read()

