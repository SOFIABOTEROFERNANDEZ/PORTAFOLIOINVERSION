"""Clase Activo: describe un instrumento financiero del portafolio."""
from dataclasses import dataclass
from typing import ClassVar, Tuple


@dataclass(frozen=True)
class Activo:
    """Instrumento de renta variable o renta fija.

    - ticker: símbolo de Yahoo Finance (KO, NKE...) o nombre libre para CDT/TES/bonos.
    - nombre: nombre descriptivo.
    - tipo: uno de Activo.TIPOS.
    """

    ticker: str
    nombre: str
    tipo: str = "Acción"

    TIPOS: ClassVar[Tuple[str, ...]] = ("Acción", "ETF", "ETF renta fija", "Bono", "CDT", "TES")
    TIPOS_RENTA_FIJA: ClassVar[Tuple[str, ...]] = ("ETF renta fija", "Bono", "CDT", "TES")
    # Instrumentos que se valoran por sus condiciones contractuales (tasa, plazo, vencimiento)
    TIPOS_CONTRACTUALES: ClassVar[Tuple[str, ...]] = ("Bono", "CDT", "TES")

    @property
    def es_renta_fija(self) -> bool:
        return self.tipo in self.TIPOS_RENTA_FIJA

    @property
    def cotiza_en_bolsa(self) -> bool:
        """True si su precio se obtiene de yfinance; False si se valora por contrato."""
        return self.tipo not in self.TIPOS_CONTRACTUALES

    @property
    def clase(self) -> str:
        return "Renta fija" if self.es_renta_fija else "Renta variable"
