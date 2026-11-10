"""Clase Operacion: registro de una transacción o flujo de caja del portafolio."""
from dataclasses import dataclass
from datetime import date
from typing import ClassVar, Dict, Optional, Tuple

import pandas as pd

from .activo import Activo

