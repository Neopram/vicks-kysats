# Quick Start — Oleadas Autónomas

## En 3 pasos:

### 1️⃣ Abre PowerShell en el directorio del repo

```powershell
cd "C:\Users\feder\Desktop\Banco de preguntas\repo_vicks"
```

### 2️⃣ Ejecuta el script

```powershell
.\launch-waves.ps1
```

### 3️⃣ Espera 25-30 minutos

El script lanzará:
- **11 oleadas** × **5 agentes Haiku** = 55 agentes
- **~1370 preguntas** bilingües (griego/español)
- Validación automática (11 reglas de calidad)
- Compilación: patologia/, pediatria/, cirugia/
- Push a GitHub Pages

## Estado esperado al terminar

```
✅ COMPLETO: 1370 preguntas generadas, compiladas, desplegadas.

Patología: 331 → ~700q (+369q)
Pediatría: 418 → ~750q (+332q)
Cirugía: 198 → ~620q (+422q)

Total: 947 → 2070q (+1123q) = 69% de cobertura
```

## Ver resultado en vivo

Una vez termina (5-10 min después del "✅ COMPLETO"):

- **Pathology:** https://neopram.github.io/vicks-kysats/patologia/
- **Pediatrics:** https://neopram.github.io/vicks-kysats/pediatria/
- **Surgery:** https://neopram.github.io/vicks-kysats/cirugia/

Cada app es instalable como PWA desde cualquier dispositivo.

---

## Troubleshooting rápido

**¿No arranca?**
- Verifica: `python --version` (debe ser 3.8+)
- Verifica: `git --version`
- Verifica: `$env:ANTHROPIC_API_KEY` (no debe estar vacía)

**¿Falla a mitad de camino?**
- Revisa %TEMP%/vicks_stage/ (¿están los JSON?)
- Ejecuta `git status` (¿hay cambios sin commitear?)
- Intenta de nuevo: `.\launch-waves.ps1`

**¿Quieres ver qué hace sin ejecutar?**
```powershell
.\launch-waves.ps1 -DryRun
```

---

**Archivo de configuración:** `OLEADAS_AUTONOMAS.md` (detalles completos)
**Script principal:** `scripts/vicks_autonomous_waves.py`
