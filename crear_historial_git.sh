set -e

[ -d .git ] && { echo "Ya existe un repositorio Git aquí. Aborta para no sobrescribirlo."; exit 1; }

git init -b main
git add .gitignore requirements.txt
git commit -m "chore: inicializa repositorio con .gitignore y dependencias"

git checkout -b develop

# ---------- feature/modelos ----------
git checkout -b feature/modelos
git add portafolio_app/__init__.py portafolio_app/activo.py
git commit -m "feat: agrega clase Activo (renta fija / renta variable)"
git add portafolio_app/operacion.py
git commit -m "feat: agrega clase Operacion con comisiones y flujo de caja"
git add portafolio_app/valorador_renta_fija.py
git commit -m "feat: agrega ValoradorRentaFija para CDT, TES y bonos"
git checkout develop
git merge --no-ff feature/modelos -m "merge: integra feature/modelos en develop"

# ---------- feature/datos-mercado ----------
git checkout -b feature/datos-mercado
git add portafolio_app/servicio_mercado.py
git commit -m "feat: agrega ServicioMercado con yfinance (precios y dividendos)"
git checkout develop
git merge --no-ff feature/datos-mercado -m "merge: integra feature/datos-mercado en develop"

# ---------- feature/calculos ----------
git checkout -b feature/calculos
git add portafolio_app/calculadora_rentabilidad.py
git commit -m "feat: agrega rentabilidad acumulada y efectiva anual (XIRR)"
git add portafolio_app/portafolio.py
git commit -m "feat: agrega Portafolio con posiciones FIFO, dividendos y resumen"
git add portafolio_app/proyeccion_anual.py portafolio_app/simulador_montecarlo.py
git commit -m "feat: agrega proyección a 1 año y simulación Monte Carlo"
git add tests/test_calculos.py
git commit -m "test: agrega pruebas unitarias de los cálculos"
git checkout develop
git merge --no-ff feature/calculos -m "merge: integra feature/calculos en develop"

# ---------- feature/dashboard ----------
git checkout -b feature/dashboard
git add portafolio_app/graficos.py
git commit -m "feat: agrega clase Graficos con figuras Plotly"
git add portafolio_app/dashboard.py main.py
git commit -m "feat: agrega Dashboard Streamlit y archivo principal main.py"
git checkout develop
git merge --no-ff feature/dashboard -m "merge: integra feature/dashboard en develop"

# ---------- docs/readme-uml ----------
git checkout -b docs/readme-uml
git add docs/generar_uml.py docs/diagrama_uml.png docs/diagrama_uml.mmd
git commit -m "docs: agrega diagrama UML generado desde el código"
git add README.md
git commit -m "docs: agrega README con instalación, uso y cálculos"
git add docs/wiki scripts
git commit -m "docs: agrega páginas de la wiki y script de historial git"
git checkout develop
git merge --no-ff docs/readme-uml -m "merge: integra documentación en develop"

# ---------- release ----------
git checkout main
git merge --no-ff develop -m "release: versión 1.0.0"
git tag -a v1.0.0 -m "Primera versión funcional"

git status --short
git log --graph --oneline --all
echo
echo "Para publicar:  git remote add origin <URL>  &&  git push -u origin --all  &&  git push --tags"
