set -e

[ -d .git ] && { echo "Ya existe un repositorio Git aquí. Aborta para no sobrescribirlo."; exit 1; }

git init -b main
git add .gitignore requirements.txt
git commit -m "chore: inicializa repositorio con .gitignore y dependencias"

git checkout -b develop
