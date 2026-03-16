from __future__ import annotations

from app.collectors.base_dos_dados import BaseDosDadosCollector
from app.collectors.base import Collector
from app.collectors.camara import CamaraCollector
from app.collectors.ibge import IBGECollector
from app.collectors.pncp import PNCPCollector
from app.collectors.portal_transparencia import PortalTransparenciaCollector
from app.collectors.senado import SenadoCollector
from app.collectors.tse import TSECollector

COLLECTORS: dict[str, Collector] = {
    "base_dos_dados": BaseDosDadosCollector(),
    "camara": CamaraCollector(),
    "ibge": IBGECollector(),
    "pncp": PNCPCollector(),
    "portal_transparencia": PortalTransparenciaCollector(),
    "senado": SenadoCollector(),
    "tse": TSECollector(),
}

