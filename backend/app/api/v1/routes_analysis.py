from __future__ import annotations

import json

from fastapi import APIRouter

from app.api.deps import DBSession
from app.schemas.api import AnalysisRequest, AnalysisResponse
from app.services.providers import ProviderService
from app.services.territory import get_city_profile

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/cities/{city_id}", response_model=AnalysisResponse)
def analyze_city(city_id: int, payload: AnalysisRequest, db: DBSession) -> AnalysisResponse:
    profile = get_city_profile(db, city_id)
    prompt = (
        "Analise os dados publicos abaixo para produzir um parecer investigativo. "
        "Inclua: 1) orgaos com maiores gastos, 2) anomalias, 3) fornecedores recorrentes, "
        "4) risco potencial de sobrepreco, 5) proximos passos de auditoria.\n\n"
        f"Pergunta do analista: {payload.question}\n\n"
        f"Resumo do territorio: {json.dumps({
            'city': profile['city'].name,
            'state': profile['state'].name,
            'totals': {k: str(v) for k, v in profile['totals'].items()},
            'agencies': len(profile['public_agencies']),
            'contracts': len(profile['contracts']),
            'spending_items': len(profile['spending']),
            'amendments': len(profile['amendments'])
        }, ensure_ascii=False)}"
    )

    provider, model_id, answer = ProviderService(db).run_analysis(prompt)
    return AnalysisResponse(provider=provider, model_id=model_id, answer=answer)

