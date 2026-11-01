# PROGRESO.md — Fraud Detection Lakehouse

> Memoria del proyecto entre sesiones. Claude Code lo lee al iniciar y lo actualiza al cerrar cada fase.
> Las reglas fijas del proyecto viven en `CLAUDE.md`; aquí solo va el avance.

---

## Estado actual

- **Fase en curso:** Fase 1 — EDA (sin empezar). Fase 0 completada.
- **Último paso completado:** `00_setup_catalog.py` terminado y probado en Databricks (catálogo, 6 esquemas, 3 Volumes)
- **Próximo paso:** ver la sección "Data Transformation" del curso y empezar `notebooks/04_eda.py` (Fase 1)
- **Última actualización:** 2026-10-31

---

## Configuración de trabajo

- **Modelo base:** Sonnet 5.5, esfuerzo medio.
- **Esfuerzo alto:** Fase 4 (ventanas sin fuga de información) y Fase 5 (partición temporal, umbral por costo, métrica top-50/día). También ADRs importantes y pitch final.
- **Opus:** solo si hay un error que Sonnet no resuelve tras un par de intentos.
- **Esfuerzo bajo:** tareas mecánicas (`PROGRESO.md`, `schema.yml`, `.gitignore`).
- Claude avisa cuándo conviene cambiar de modelo o esfuerzo.

---

## Curso de Databricks

| Sección | Antes de | Visto |
|---|---|---|
| Introduction + Databricks Intelligence Platform (secciones 1–2) | Fase 0 | [x] |
| Data Governance & Quality, clases de Unity Catalog (sección 7 del curso) | Fase 0 | [ ] pendiente |
| Data Transformation | Fase 1 | [ ] |
| Data Ingestion and Loading | Fase 2 | [ ] |
| Incremental Data Processing | Fase 2 | [ ] |
| Data Governance & Quality (resto) | Fase 3 | [ ] |
| Productionizing Data Pipelines | Fase 6 | [ ] |
| Certification Overview | Después de Fase 9 | [ ] |

---

## Checklist por fase

### Fase 0 — Preparación (COMPLETADA 2026-10-31)
- [x] Repo en GitHub (ramas `main` y `dev`) conectado como Git folder en Databricks (rama `dev`)
- [x] `notebooks/00_setup_catalog.py` (catálogo `fraud_lakehouse` + esquemas, idempotente, con verificación)
- [x] Volumes de `landing` creados (`source_full`, `source_by_hour`, `incoming`)
- [x] PaySim descargado y subido a `landing.source_full/paysim.csv` (6.362.620 filas verificadas con `read_files`)
- [x] `.gitignore` y carpetas base (`notebooks/`, `docs/decisiones/`)
- [x] `docs/caso_de_negocio.md` escrito en mis palabras
- [x] Python 3.12 + `.venv` + `dbt-databricks` (dbt-core 1.12.6, adaptador 1.13.0); `profiles.yml` en `~/.dbt/` (fuera del repo); `dbt debug` pasa
- [x] Databricks CLI 1.22.1 instalado (falta autenticarlo; se hace en la Fase 2/6 cuando se use)
- [x] `dbt/fraud_dbt/dbt_project.yml` mínimo (sin modelos todavía)
- **DoD:** `SELECT` sobre el CSV desde el Volume funciona; `dbt debug` pasa; caso de negocio escrito.

### Fase 1 — EDA
- [ ] `notebooks/04_eda.py`
- [ ] Hallazgos en `docs/diccionario_de_datos.md`
- [ ] Riesgos de fuga de información identificados
- **DoD:** 5–8 hallazgos con gráfico; features candidatas y columnas prohibidas.

### Fase 2 — Simulación de llegada + Bronze (Auto Loader)
- [ ] `01_split_by_step.py`
- [ ] `02_arrival_simulator.py` + `ops.simulator_state`
- [ ] `03_bronze_autoloader.py`
- [ ] Prueba de idempotencia
- [ ] Prueba de archivo corrupto (`_rescued_data`)
- [ ] ADR: Auto Loader vs COPY INTO
- **DoD:** 3 corridas = 72 horas en bronze sin duplicados; prueba documentada.

### Fase 3 — Silver con dbt
- [ ] `sources.yml` con freshness
- [ ] `silver.transactions` (incremental, merge)
- [ ] `silver.accounts`
- [ ] Tests (unique, not_null, accepted_values, amount >= 0, test singular de negocio)
- [ ] `dbt docs` con linaje
- [ ] ADR: dbt vs Lakeflow Declarative Pipelines
- **DoD:** `dbt build --select silver` pasa; captura del linaje.

### Fase 4 — Gold: features y reglas AML (esfuerzo alto)
- [ ] `gold.transaction_features` (ventanas solo hacia atrás)
- [ ] `gold.aml_rule_hits` (5 tipologías) + `docs/reglas_aml.md`
- [ ] Desempeño de cada regla vs `isFraud`
- [ ] Test anti-fuga
- **DoD:** tabla de desempeño por regla; ninguna feature usa información futura.

### Fase 5 — Modelo ML con MLflow (esfuerzo alto)
- [ ] Partición temporal
- [ ] Línea base (regresión logística) + gradient boosting
- [ ] Métricas: PR-AUC, recall a precisión fija, dinero capturado en top 50/día
- [ ] Umbral por costo
- [ ] Modelo registrado en UC (`fraud_lakehouse.ml.fraud_classifier`, alias `champion`)
- [ ] Comparación reglas vs modelo vs `isFlaggedFraud`
- [ ] `06_batch_scoring.py` incremental
- **DoD:** ≥ 2 corridas comparables en MLflow; tabla comparativa; scoring incremental.

### Fase 6 — Cola de alertas, orquestación y operación
- [ ] `gold.alert_queue`
- [ ] `gold.kpi_daily`
- [ ] Job en Lakeflow Jobs con tareas dependientes
- [ ] `07_pipeline_metrics.py` + `ops.pipeline_runs`
- [ ] Job como código (`databricks.yml`, `resources/jobs.yml`)
- **DoD:** job corre de punta a punta; si falla un test dbt, se detiene y reporta.

### Fase 7 — Tablero Streamlit
- [ ] `08_export_snapshot.py`
- [ ] `app/data_access.py` (snapshot | live)
- [ ] Páginas: resumen, alertas, salud del pipeline
- [ ] Publicada en Streamlit Community Cloud
- [ ] Capturas en `docs/img/`
- [ ] ADR: Streamlit + snapshot vs Databricks Apps vs AI/BI
- **DoD:** app pública sin login; ambos modos funcionan; `secrets.toml` en `.gitignore`.

### Fase 8 — CI y calidad de código
- [ ] GitHub Actions: sqlfluff, `dbt parse`, pytest
- [ ] Tests unitarios de `src/`
- [ ] Trabajo con ramas y PRs
- **DoD:** CI en verde con badge en el README.

### Fase 9 — Empaquetado para entrevistas
- [ ] `README.md` (inglés) y `README.es.md`
- [ ] Video demo 3–5 min
- [ ] Portafolio web y CV
- [ ] Post de LinkedIn
- [ ] Pitch STAR con números reales
- **DoD:** un amigo sin contexto entiende el proyecto leyendo el README.

---

## Qué aprendí

(Se completa al cerrar cada fase.)

### Fase 0 (cerrada)
- Unity Catalog: jerarquía catálogo → esquema → objeto (tablas, Volumes); nombres de tres niveles.
- Idempotencia con `IF NOT EXISTS`; widgets para parámetros; notebooks como `.py` (texto plano, mejor para Git).
- Flujo de Git: escribo en el PC → commit/push a `dev` → Pull en Databricks → PR `dev` → `main` al cerrar un bloque → `git pull origin main` en `dev`.

---

## Decisiones tomadas

| Fecha | Decisión | ADR |
|---|---|---|
| 2026-10-31 | Usar Sonnet 5.5 con esfuerzo medio como base; subir en fases 4 y 5 | — |
| 2026-10-31 | `PROGRESO.md` como memoria entre sesiones; `CLAUDE.md` para reglas fijas | — |
| 2026-10-31 | Ramas `main` (estable) y `dev` (trabajo); PR de `dev` a `main` con merge normal, no squash | — |
| 2026-10-31 | El código se escribe solo en el PC; el Git folder de Databricks solo hace Pull y ejecuta | — |

---

## Bitácora de errores

(Error de Databricks → causa → solución. Sirve para preguntas de entrevista.)

- **Conflicto al hacer Pull en el Git folder** ("Conflict(s) from pull", "Error continue merge: tip of your current branch is behind remote").
  - Causa: la copia de Databricks tenía cambios sin subir y, además, `main` y `dev` divergieron tras fusionar un PR.
  - Solución: no resolver conflictos en Databricks; borrar y recrear el Git folder (todo está en GitHub). En el PC, `git pull origin main` en `dev` justo después de cada merge.
  - Pendiente: confirmar por qué Databricks modifica el archivo tras ejecutarlo.
