"""Archivo principal: desde aquí se cargan todas las demás clases.

Ejecutar con:
    streamlit run main.py
"""
from portafolio_app.dashboard import Dashboard


def main() -> None:
    Dashboard().ejecutar()


main()
