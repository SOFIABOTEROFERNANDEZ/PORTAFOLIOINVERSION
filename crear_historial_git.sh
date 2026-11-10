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
