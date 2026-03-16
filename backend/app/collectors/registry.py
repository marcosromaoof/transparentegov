from __future__ import annotations

from app.collectors.base import Collector
from app.collectors.camara import CamaraCollector
from app.collectors.ibge import IBGECollector

COLLECTORS: dict[str, Collector] = {
    "camara": CamaraCollector(),
    "ibge": IBGECollector(),
}

