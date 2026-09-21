#!/usr/bin/env bash
# Compila las tres apps de materia y las copia al repo.
#
# Windows Controlled Folder Access impide que python.exe cree archivos dentro
# de Desktop, asi que python escribe en %TEMP%/vicks_build y este script copia
# el resultado con cp, que si esta permitido.
#
#   ./scripts/build.sh            # valida y compila A, B y C
#   ./scripts/build.sh B          # solo Pediatria
#   ./scripts/build.sh --no-check # compila sin pasar la puerta de calidad
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"
OUT="${TEMP:-/tmp}/vicks_build"
export VICKS_ROOT="$ROOT"
export PYTHONIOENCODING=utf-8

CHECK=1
SPECS=()
for a in "$@"; do
  case "$a" in
    --no-check) CHECK=0 ;;
    A|B|C) SPECS+=("$a") ;;
    *) echo "argumento desconocido: $a" >&2; exit 2 ;;
  esac
done
[ ${#SPECS[@]} -eq 0 ] && SPECS=(A B C)

if [ "$CHECK" = 1 ]; then
  echo "== puerta de calidad =="
  python scripts/validate_bank.py "${SPECS[@]}"
fi

echo "== compilando =="
python scripts/build_v6.py "${SPECS[@]}"

echo "== copiando al repo =="
for s in "${SPECS[@]}"; do
  case "$s" in
    A) d=patologia ;;
    B) d=pediatria ;;
    C) d=cirugia ;;
  esac
  mkdir -p "$ROOT/$d"
  cp "$OUT/$d/index.html"    "$ROOT/$d/index.html"
  cp "$OUT/$d/sw.js"         "$ROOT/$d/sw.js"
  cp "$OUT/$d/manifest.json" "$ROOT/$d/manifest.json"
  printf '   %-10s %8d bytes\n' "$d" "$(wc -c < "$ROOT/$d/index.html")"
done

echo "== comprobacion final =="
python scripts/check_build.py "${SPECS[@]}"
