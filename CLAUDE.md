# CLAUDE.md — Fraud Detection Lakehouse (AML) en Databricks

> Archivo de contexto para Claude Code. Léelo completo antes de proponer o escribir código.
> Autor del proyecto: Carlos Mario Hoyos Ríos — Desarrollador BI / Ingeniero de Datos (Cali, Colombia).

---

## 1. Qué es este proyecto (en una frase)

Un **lakehouse de punta a punta en Databricks** que simula la operación de monitoreo de fraude y
lavado de activos (AML) de un banco digital: recibe transacciones en lotes que llegan cada "hora",
las limpia con arquitectura medallion, genera reglas AML y un modelo de ML, produce **alertas
priorizadas para analistas** y muestra los resultados de negocio en un tablero.

Es el **proyecto principal del portafolio** y la carta de presentación para entrevistas de
Data Engineer / Analytics Engineer (Colombia e internacional).

---

## 2. Cómo debe trabajar Claude Code conmigo (MUY IMPORTANTE)

0. **Al iniciar cada sesión, lee `PROGRESO.md`** y dime en qué fase y paso estamos. Avísame cuándo
   conviene cambiar de modelo o esfuerzo (ver "Configuración de trabajo" en `PROGRESO.md`).
1. **Modo mentor, no modo piloto automático.** Yo tengo que poder explicar cada línea en una
   entrevista. Antes de escribir código de una tarea nueva: explica en 3–6 frases qué vamos a hacer
   y por qué, luego escribe el código, luego dime qué debo ejecutar y qué resultado esperar.
2. **Una fase a la vez.** No adelantes trabajo de fases futuras. No generes todo el repo de golpe.
3. **Yo ejecuto en Databricks.** Claude Code escribe archivos en el repo; yo corro notebooks, jobs
   y comandos en el workspace y le paso los errores.
4. **Al cerrar cada fase:** actualiza `PROGRESO.md` (checklist + qué aprendí + decisiones tomadas)
   y, si hubo una decisión de diseño relevante, crea un ADR en `docs/decisiones/`.
5. **Pídeme permiso una sola vez por bloque**: dime la lista exacta de archivos que vas a crear o
   modificar, yo autorizo, y lo haces todo seguido sin preguntar en cada paso.
6. **Aprendo experimentando.** Cuando haya un concepto nuevo (Auto Loader, checkpoints, modelos
   incrementales de dbt, MLflow), dame un ejemplo mínimo para probar antes de la versión completa.
7. **Honestidad del proyecto:** los datos son sintéticos (PaySim). Nunca escribas en el README ni
   en textos públicos que son datos reales de un banco. **Nunca usar datos, nombres de tablas,
   reglas ni lógica de mi empleo actual.** El banco del caso es ficticio.
8. **Textos públicos (README, post de LinkedIn):** tono modesto pero sin desmeritar el trabajo; no
   prometer funcionalidades que no estén construidas.
9. Si propongo algo que agranda el alcance sin aportar a conseguir entrevistas, dímelo claramente.

---

## 3. El caso de negocio (lo que hace que parezca un caso real)

**Empresa ficticia:** *Banco Andino Digital* — banco digital con billetera móvil que opera
transferencias, retiros (cash-out), pagos y depósitos.

**Problema:** el área de Prevención de Fraude y Cumplimiento (AML) revisa transacciones de forma
manual y tardía. El fraude típico es **toma de cuenta**: el atacante transfiere el saldo de la
víctima a una cuenta "mula" (TRANSFER) y la vacía con un retiro (CASH_OUT). Además, regulación
alineada con las recomendaciones del **GAFI/FATF** exige monitoreo de transacciones y reporte de
operaciones sospechosas.

**Restricción operativa (clave para el diseño):** el equipo tiene capacidad para revisar un
número limitado de alertas por día (supuesto: **50 alertas/día**). No sirve un sistema que
dispare miles de alertas.

**Objetivo del proyecto:** entregar cada hora (lote) una **cola de alertas priorizada** que
combine reglas AML explicables + un score de ML, y medir el impacto en dinero.

**KPIs que el tablero debe mostrar:**
- Monto de fraude detectado vs. monto de fraude no detectado (dinero "salvado").
- Recall (fraude atrapado) y precisión de las alertas (qué % de alertas eran fraude real).
- Alertas por día vs. capacidad del equipo (50/día).
- Distribución de alertas por tipología AML.
- Latencia del pipeline: tiempo desde que llega el lote hasta que la alerta está disponible.
- Salud de los datos: filas ingeridas, filas rechazadas, tests de calidad pasados/fallidos.

---

## 4. Datos

- **Dataset:** PaySim (Kaggle, "Synthetic Financial Datasets For Fraud Detection").
  ~6.3 millones de filas, ~470 MB en CSV, 30 días simulados.
- **Columnas:** `step` (hora 1–743), `type` (CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER),
  `amount`, `nameOrig`, `oldbalanceOrg`, `newbalanceOrig`, `nameDest`, `oldbalanceDest`,
  `newbalanceDest`, `isFraud`, `isFlaggedFraud`.
- **Hechos conocidos a validar con EDA (no asumir, comprobar):** el fraude es muy poco frecuente
  (~0.1%) y aparece solo en TRANSFER y CASH_OUT; las cuentas que empiezan con `M` son comercios;
  `isFlaggedFraud` es una regla ingenua del sistema original (transferencias > 200.000).
- **Carga:** el internet de salida en Databricks Free Edition está restringido, así que el CSV se
  descarga en mi PC y se sube manualmente a un Volume de Unity Catalog (UI o Databricks CLI).
- **Tiempo:** convertir `step` en timestamp real: `fecha_base + step horas`
  (fecha_base = `2026-01-01 00:00:00`, zona America/Bogota). Documentarlo como supuesto.

---

## 5. Stack y restricciones de la plataforma

| Capa | Herramienta |
|---|---|
| Plataforma | Databricks **Free Edition** (solo serverless, Unity Catalog) |
| Almacenamiento | Delta Lake + Unity Catalog Volumes |
| Ingesta | Auto Loader (`cloudFiles`) con `trigger(availableNow=True)` |
| Transformación | dbt Core con `dbt-databricks` contra el SQL Warehouse |
| ML | scikit-learn (+ XGBoost/LightGBM si instala sin problema), MLflow, registro de modelos en Unity Catalog |
| Orquestación | Lakeflow Jobs (antes "Workflows"): tareas de notebook + tarea dbt |
| Infra como código | Declarative Automation Bundles (antes "Asset Bundles"), `databricks.yml` |
| CI | GitHub Actions (lint SQL, `dbt parse`, tests de Python) |
| Visualización | App en **Streamlit** (+ Plotly), publicada gratis en Streamlit Community Cloud; modo *snapshot* (Parquet en el repo) y modo *en vivo* (SQL Warehouse vía `databricks-sql-connector`) |
| Control de versiones | GitHub + Git folders en Databricks |

**Límites de Free Edition que el diseño debe respetar:**
- Solo cómputo serverless; sin clusters personalizados ni GPU. Sin R ni Scala → todo en Python/SQL.
- Un solo SQL Warehouse tamaño 2X-Small → modelos dbt eficientes, nada de full refresh innecesario.
- Máximo 5 tareas de jobs concurrentes.
- Cuota diaria de uso: si se excede, el cómputo se apaga hasta el día siguiente → trabajar con
  muestras durante desarrollo y el dataset completo solo en corridas finales.
- Streaming en serverless: usar `availableNow` (procesamiento por lotes incremental), no streaming continuo.
- Internet de salida restringido a dominios confiables.

---

## 6. Arquitectura objetivo

```
[PaySim CSV en mi PC]
        │ (subida manual)
        ▼
Volume: fraud_lakehouse.landing.source_full      ← archivo completo, nunca se toca
        │  notebook 01_split_by_step (una sola vez)
        ▼
Volume: fraud_lakehouse.landing.source_by_hour   ← un archivo por step (hora)
        │  notebook 02_arrival_simulator (cada corrida mueve las próximas N horas)
        ▼
Volume: fraud_lakehouse.landing.incoming         ← "lo que el core bancario envía"
        │  Auto Loader (availableNow) + checkpoint
        ▼
BRONZE  bronze.transactions_raw   (todo como llegó + _source_file, _ingested_at, _rescued_data)
        │  dbt (incremental)
        ▼
SILVER  silver.transactions       (tipos correctos, timestamp, dedupe, columnas derivadas)
        silver.accounts           (dimensión de cuentas: cliente vs comercio, primera/última actividad)
        │  dbt
        ▼
GOLD    gold.transaction_features (features por transacción y ventanas por cuenta)
        gold.aml_rule_hits        (una fila por regla disparada)
        gold.fraud_scores         (score del modelo, escrito por notebook de scoring)
        gold.alert_queue          (reglas + score → prioridad, top N por día)
        gold.kpi_daily            (métricas de negocio para el tablero)
        │
        ├── ML: notebook de entrenamiento → MLflow → modelo registrado en UC (alias "champion")
        ├── notebook 08_export_snapshot → Parquet de gold/ops → carpeta app/data/ del repo
        └── App Streamlit (modo snapshot = público | modo en vivo = SQL Warehouse)

OPS     ops.pipeline_runs         (filas por capa, duración, estado de cada corrida)
```

**Catálogo y esquemas:** `fraud_lakehouse` con esquemas `landing`, `bronze`, `silver`, `gold`, `ml`, `ops`.

---

## 7. Estructura del repositorio

```
fraud-detection-lakehouse/
├── CLAUDE.md
├── README.md                  # en inglés (reclutadores internacionales)
├── README.es.md               # versión en español
├── PROGRESO.md                # checklist por fase + aprendizajes
├── databricks.yml             # bundle: jobs como código
├── resources/
│   └── jobs.yml
├── notebooks/
│   ├── 00_setup_catalog.py
│   ├── 01_split_by_step.py
│   ├── 02_arrival_simulator.py
│   ├── 03_bronze_autoloader.py
│   ├── 04_eda.py
│   ├── 05_train_model.py
│   ├── 06_batch_scoring.py
│   ├── 07_pipeline_metrics.py
│   └── 08_export_snapshot.py
├── dbt/fraud_dbt/
│   ├── dbt_project.yml
│   ├── models/
│   │   ├── sources.yml
│   │   ├── silver/  (transactions.sql, accounts.sql, schema.yml)
│   │   └── gold/    (transaction_features.sql, aml_rule_hits.sql, alert_queue.sql, kpi_daily.sql, schema.yml)
│   ├── macros/
│   └── tests/       (tests singulares de negocio)
├── src/fraud_lakehouse/       # funciones Python reutilizables (con tests)
├── tests/                     # pytest
├── app/                       # tablero en Streamlit
│   ├── streamlit_app.py       # página principal (resumen ejecutivo)
│   ├── pages/                 # 2_Alertas.py, 3_Salud_del_pipeline.py
│   ├── data_access.py         # capa única de acceso: snapshot o en vivo
│   ├── data/                  # Parquet del snapshot (pocos MB, sí va al repo)
│   ├── requirements.txt
│   └── .streamlit/            # config.toml (tema); secrets.toml NUNCA al repo
├── docs/img/                  # capturas de la app para el README
├── docs/
│   ├── arquitectura.png
│   ├── caso_de_negocio.md
│   ├── diccionario_de_datos.md
│   ├── reglas_aml.md
│   └── decisiones/            # ADR-001-..., ADR-002-...
└── .github/workflows/ci.yml
```

**Convenciones:** código, tablas y columnas en inglés (`snake_case`); comentarios y documentación
interna pueden estar en español. Commits pequeños con mensajes claros (`feat:`, `fix:`, `docs:`).

---

## 8. Fases

Cada fase tiene: objetivo, tareas, entregable y **Definición de Terminado (DoD)**. No se pasa a la
siguiente fase sin cumplir el DoD.

### Mapa del curso de Databricks por fase

Estoy siguiendo un curso de Databricks Data Engineer (8 secciones, ~6 h) alineado con la
certificación. Lo veo **por secciones, justo antes de la fase donde lo aplico**, no completo de una vez.

| Sección del curso | Antes de | Qué aplico |
|---|---|---|
| Introduction + Databricks Intelligence Platform | Fase 0 | Workspace, Unity Catalog, catálogos, esquemas, Volumes |
| Data Governance & Quality (clases de Unity Catalog) | Fase 0 | Organización y permisos de `fraud_lakehouse` |
| Data Transformation | Fase 1 (y luego 3–4) | PySpark/SQL para el EDA; ventanas y joins en silver/gold |
| Data Ingestion and Loading | Fase 2 | COPY INTO vs. Auto Loader (ADR) |
| Incremental Data Processing | Fase 2 | Auto Loader, checkpoints, `availableNow` |
| Data Governance & Quality (resto) | Fase 3 | Calidad de datos → tests de dbt |
| Productionizing Data Pipelines | Fase 6 | Lakeflow Jobs, dependencias, reintentos, bundles |
| Certification Overview | Después de Fase 9 | Preparación del examen |

**Reglas para Claude Code sobre el curso:**
- Antes de una fase, pregúntame si ya vi la sección del curso que le corresponde. Si no la he
  visto, recomiéndame verla primero (no es bloqueante si decido avanzar).
- Los ejemplos del curso los replico en un notebook de práctica **fuera del repo**; al repo solo
  llega el código del proyecto.
- Si el curso usa algo que no funciona en Free Edition (clusters clásicos, `/dbfs`, Scala),
  explícame el equivalente en serverless + Volumes y anótalo como posible pregunta de entrevista.
- Si el curso enseña Lakeflow Declarative Pipelines (antes DLT), propón un ejemplo mínimo de
  práctica para sustentar el ADR "dbt vs. Declarative Pipelines" y para la certificación, sin
  meterlo al pipeline del proyecto.
- Lo que el curso no cubre (dbt, MLflow, Streamlit, CI) lo aprendo en el proyecto con la
  documentación oficial y con explicaciones tuyas en modo mentor.

### Fase 0 — Preparación (≈ 1 semana)
**Objetivo:** entorno listo y caso de negocio escrito antes de tocar datos.
- Crear repo en GitHub y conectarlo como Git folder en Databricks.
- Crear catálogo `fraud_lakehouse` y esquemas (notebook `00_setup_catalog.py`, idempotente).
- Crear Volumes de `landing`.
- Descargar PaySim y subirlo a `landing.source_full`.
- Escribir `docs/caso_de_negocio.md` (sección 3 de este archivo, en mis palabras).
- Instalar en local: Databricks CLI, `dbt-databricks`, configurar `profiles.yml` contra el SQL Warehouse (sin subir credenciales al repo; `.gitignore`).

**DoD:** `SELECT` sobre el CSV desde el Volume funciona; `dbt debug` pasa en local; caso de negocio escrito.

### Fase 1 — Exploración de datos (EDA) (≈ 1 semana)
**Objetivo:** entender los datos y justificar decisiones con evidencia.
- Notebook `04_eda.py` con: conteos por `type`, tasa de fraude por tipo, distribución de montos,
  comportamiento de saldos en fraudes vs. no fraudes, patrón TRANSFER→CASH_OUT, cuentas destino
  que reciben muchas transacciones, calidad de `isFlaggedFraud` (precisión/recall de esa regla).
- Anotar hallazgos en `docs/diccionario_de_datos.md` y en `PROGRESO.md`.
- Identificar **riesgos de fuga de información** (data leakage): columnas de saldo que el simulador
  deja inconsistentes en fraudes, IDs de cuenta, `isFlaggedFraud`.

**DoD:** 5–8 hallazgos escritos con su gráfico; lista de features candidatas y de columnas prohibidas para el modelo.

### Fase 2 — Simulación de llegada + Bronze con Auto Loader (≈ 1–2 semanas)
**Objetivo:** que los datos lleguen como en un banco real: por lotes horarios, de forma incremental.
- `01_split_by_step.py`: dividir el CSV en un archivo por `step` (una sola vez).
- `02_arrival_simulator.py`: parámetro `hours_per_run` (ej. 24); mueve las próximas N horas a
  `incoming` y registra hasta qué step va en una tabla `ops.simulator_state`.
- `03_bronze_autoloader.py`: Auto Loader con esquema explícito o `schemaHints`,
  `rescuedDataColumn`, columnas de metadatos (`_source_file`, `_ingested_at`), checkpoint en
  Volume, `trigger(availableNow=True)`, escribe `bronze.transactions_raw`.
- Probar idempotencia: correr dos veces seguidas no duplica filas.
- Inyectar a propósito 1 archivo con una columna corrupta para demostrar `_rescued_data`.

**DoD:** 3 corridas del simulador = 72 horas en bronze sin duplicados; prueba de archivo corrupto documentada.
**ADR sugerido:** por qué Auto Loader y no `COPY INTO` ni lectura batch completa.

### Fase 3 — Silver con dbt (≈ 1–2 semanas)
**Objetivo:** datos limpios, confiables y probados.
- `sources.yml` apuntando a bronze, con `freshness` sobre `_ingested_at`.
- `silver.transactions` (**incremental**, `merge` por clave única): tipos correctos,
  `transaction_ts` desde `step`, `transaction_id` determinístico (hash de columnas), flags
  `is_merchant_dest`, `orig_balance_error`, `dest_balance_error`, `is_account_drained`.
- `silver.accounts`: una fila por cuenta, tipo (cliente/comercio), primera y última transacción, volumen total.
- Tests: `unique`, `not_null`, `accepted_values` en `type`, `amount >= 0`, test singular de
  negocio (ej. "no hay fraudes fuera de TRANSFER/CASH_OUT" — si falla, se investiga, no se borra).
- Generar `dbt docs` con el linaje.

**DoD:** `dbt build --select silver` pasa con todos los tests; captura del grafo de linaje.
**ADR sugerido:** dbt vs. Lakeflow Declarative Pipelines (Free Edition permite un pipeline activo por tipo; dbt es más común en ofertas y portable).

### Fase 4 — Gold: features y reglas AML (≈ 2 semanas)
**Objetivo:** convertir datos en señales de riesgo explicables.
- `gold.transaction_features`: por transacción, con ventanas **solo hacia atrás** (sin mirar el futuro):
  - número y monto de transacciones de la cuenta origen en la última 1h y 24h,
  - ratio `amount / oldbalanceOrg`, cuenta vaciada,
  - número de remitentes distintos que recibió la cuenta destino en las últimas 24h,
  - si la cuenta destino hizo un CASH_OUT poco después de recibir un TRANSFER,
  - tipo de transacción, hora del día.
- `gold.aml_rule_hits` — tipologías documentadas en `docs/reglas_aml.md`, cada una con su justificación:
  1. **Vaciado de cuenta (account takeover):** TRANSFER que deja el saldo en 0 seguido de CASH_OUT del mismo monto.
  2. **Cuenta mula / embudo:** cuenta destino que recibe de muchos orígenes distintos en poco tiempo.
  3. **Fraccionamiento (structuring):** varias transacciones justo por debajo de un umbral en una ventana corta.
  4. **Monto alto inusual:** monto muy por encima del histórico de la cuenta.
  5. **Movimiento rápido:** entrada y salida de fondos en la misma cuenta en < N horas.
- Medir cada regla contra `isFraud`: precisión, recall y alertas/día. Ajustar umbrales con datos.

**DoD:** tabla con desempeño de cada regla; ninguna feature usa información posterior a la transacción (test que lo verifique).

### Fase 5 — Modelo de ML con MLflow (≈ 2 semanas)
**Objetivo:** un score que mejore las reglas, evaluado como lo haría un banco. (El foco del
proyecto es ingeniería de datos; el modelo debe ser correcto y bien evaluado, no sofisticado.)
- Solo TRANSFER y CASH_OUT (donde existe el fraude). Documentarlo.
- **Partición temporal**, no aleatoria: entrenar con los primeros ~20 días, validar y probar con los últimos.
- Línea base: regresión logística. Modelo principal: gradient boosting.
- Desbalance: `class_weight` o ajuste de umbral; nada de accuracy como métrica.
- Métricas: **PR-AUC**, recall con precisión fija, y **métrica de negocio**: dinero de fraude
  capturado dentro de las top 50 alertas/día.
- Elegir umbral por costo (pérdida por fraude no detectado vs. costo de revisar una alerta).
- Registrar todo en MLflow (parámetros, métricas, gráficos, modelo) y registrar el modelo en
  Unity Catalog `fraud_lakehouse.ml.fraud_classifier` con alias `champion`.
- Comparar el modelo contra las reglas de la fase 4 y contra `isFlaggedFraud`.
- `06_batch_scoring.py`: carga el modelo por alias, puntúa solo las transacciones nuevas y escribe `gold.fraud_scores`.

**DoD:** experimento en MLflow con ≥ 2 corridas comparables; tabla "reglas vs. modelo vs. regla original"; scoring incremental funcionando.

### Fase 6 — Cola de alertas, orquestación y operación (≈ 1–2 semanas)
**Objetivo:** que todo corra solo, como en producción.
- `gold.alert_queue`: combina reglas + score en una prioridad; limita a la capacidad diaria; guarda el motivo de cada alerta (explicabilidad para el analista).
- `gold.kpi_daily`: KPIs de la sección 3.
- Job en Lakeflow Jobs con tareas dependientes:
  `simulator → bronze_autoloader → dbt_build (silver+gold+tests) → batch_scoring → dbt (alert_queue, kpi_daily) → pipeline_metrics`.
- Reintentos, notificación por correo si falla, parámetros del job (`hours_per_run`).
- `07_pipeline_metrics.py`: registra filas por capa, duración y estado en `ops.pipeline_runs`.
- Definir el job en `databricks.yml` / `resources/jobs.yml` y desplegarlo con `databricks bundle deploy`.
- Programar el job (ej. cada hora durante una demo, o manual) — cuidar la cuota diaria.

**DoD:** el job completo corre de punta a punta sin intervención; si un test de dbt falla, el job se detiene y lo reporta; job definido como código.

### Fase 7 — Tablero en Streamlit (≈ 1–2 semanas)
**Objetivo:** que un gerente entienda el valor en 30 segundos y que **cualquier reclutador lo
pueda abrir con un link**, sin cuenta de Databricks.

**Por qué modo dual (decisión de diseño → ADR):**
- Databricks Apps en Free Edition se apaga sola a las 24 h y exige iniciar sesión en mi
  workspace → un reclutador no la puede ver.
- Streamlit Community Cloud da un link público gratis, pero si consultara el SQL Warehouse en cada
  visita gastaría mi cuota diaria y expondría un token.
- Solución: **modo snapshot** por defecto (lee Parquet exportado de gold/ops) y **modo en vivo**
  activado con una variable de entorno (consulta el SQL Warehouse). El link público usa snapshot;
  el video demo muestra el modo en vivo.

**Tareas:**
- `notebooks/08_export_snapshot.py`: exporta `gold.kpi_daily`, `gold.alert_queue` (últimos días),
  resumen de `gold.aml_rule_hits`, comparación de modelos y `ops.pipeline_runs` a Parquet pequeño
  (objetivo < 20 MB en total; nada de transacciones crudas). Se descarga y se guarda en `app/data/`.
- `app/data_access.py`: una sola capa de acceso. Variable `DATA_MODE=snapshot|live`.
  - `snapshot`: lee Parquet con pandas.
  - `live`: usa `databricks-sql-connector` con host, http_path y token leídos de `st.secrets`
    o variables de entorno (nunca en el código).
  - Cachear con `st.cache_data` (TTL) para no repetir consultas.
- Páginas:
  1. **Resumen ejecutivo** (`streamlit_app.py`): KPIs en tarjetas (dinero detectado vs. perdido,
     recall, precisión, alertas/día vs. capacidad de 50), tendencia diaria, comparación
     reglas vs. modelo vs. regla original.
  2. **Alertas** (`pages/2_Alertas.py`): cola del día con filtros (fecha, tipología, score),
     motivo de cada alerta y detalle de la transacción al seleccionarla.
  3. **Salud del pipeline** (`pages/3_Salud_del_pipeline.py`): filas por capa, latencia,
     tests de calidad, última corrida.
- Gráficos con Plotly; tema visual consistente en `.streamlit/config.toml`.
- Banner visible en la app: "Datos sintéticos (PaySim) — banco ficticio — snapshot del {fecha}".
- Publicar en Streamlit Community Cloud desde el repo de GitHub (carpeta `app/`).
- Capturas en `docs/img/` para el README.

**DoD:** app pública abre por link sin login; funciona en modo snapshot y en modo en vivo en local;
`secrets.toml` en `.gitignore`; capturas en el repo.
**ADR sugerido:** Streamlit Community Cloud + snapshot vs. Databricks Apps vs. dashboard AI/BI.

### Fase 8 — CI y calidad de código (≈ 1 semana)
- GitHub Actions en cada pull request: `sqlfluff lint` (dialecto databricks), `dbt parse`, `pytest` sobre `src/`.
- Tests unitarios de las funciones Python (ej. generación de `transaction_id`, lógica del simulador).
- Trabajar con ramas y PRs (aunque sea solo), para mostrar flujo profesional.

**DoD:** CI en verde con badge en el README.

### Fase 9 — Empaquetado para entrevistas (≈ 1 semana) — LA MÁS IMPORTANTE
**Objetivo:** que un reclutador entienda el proyecto en 2 minutos y un técnico en 10.
- `README.md` (inglés) con este orden:
  1. Título + una línea del problema de negocio + **link a la app de Streamlit** arriba de todo.
  2. Resultados con números (ej. "las top 50 alertas diarias capturan X% del dinero en fraude").
  3. Diagrama de arquitectura.
  4. Stack.
  5. Cómo funciona cada capa (corto).
  6. Decisiones de diseño y trade-offs (enlaces a ADRs).
  7. Limitaciones honestas (datos sintéticos, Free Edition, batch y no tiempo real).
  8. Cómo ejecutarlo.
  9. Qué haría distinto en producción (sin prometer que lo voy a construir).
- `README.es.md` en español.
- Video demo de 3–5 minutos: problema → arquitectura → job corriendo → app de Streamlit en modo en vivo → una decisión técnica.
- Agregarlo a mi web portafolio (GitHub Pages) y al CV en la sección de proyectos.
- Post de LinkedIn (tono modesto, sin exagerar).
- Preparar mi pitch STAR (sección 10).

**DoD:** un amigo sin contexto entiende el proyecto leyendo solo el README; puedo explicar el proyecto en 2 minutos sin leer.

---

## 9. Qué voy a mostrar (resumen de entregables)

1. Repo público en GitHub con código, tests, CI y documentación.
2. Arquitectura medallion con ingesta incremental real (Auto Loader + simulador de llegadas).
3. Transformaciones en dbt con tests de calidad y linaje.
4. Reglas AML explicables alineadas con tipologías GAFI/FATF, medidas con datos.
5. Modelo de ML evaluado sin fuga de información, con métrica de negocio, en MLflow.
6. Orquestación como código (Lakeflow Jobs + bundle).
7. App en Streamlit con link público (resumen ejecutivo, cola de alertas, salud del pipeline).
8. ADRs con decisiones y trade-offs.
9. Video demo + README + post.

**Habilidades que el proyecto demuestra (para mapear contra ofertas):** Databricks, Delta Lake,
Unity Catalog, PySpark, SQL, dbt, ingesta incremental, calidad de datos, orquestación, MLflow,
CI/CD, modelado dimensional, Streamlit / visualización con Python, conocimiento del dominio financiero/AML, comunicación de resultados.

---

## 10. Pitch de entrevista (borrador, completar al final con números reales)

- **Situación:** los bancos digitales necesitan detectar fraude y operaciones sospechosas a tiempo, con equipos de revisión limitados.
- **Tarea:** construir un pipeline que entregue alertas priorizadas cada hora, respetando una capacidad de 50 alertas/día.
- **Acción:** lakehouse en Databricks con ingesta incremental, dbt con tests, reglas AML + modelo en MLflow, orquestado como código.
- **Resultado:** [completar: % del dinero en fraude capturado, precisión de alertas, comparación vs. regla original].

**Preguntas que debo poder responder:**
- ¿Por qué partición temporal y no aleatoria?
- ¿Cómo evitas fuga de información en las features?
- ¿Qué pasa si llega un archivo duplicado o corrupto?
- ¿Por qué dbt y no Lakeflow Declarative Pipelines?
- ¿Cómo lo escalarías a tiempo real?
- ¿Por qué PR-AUC y no accuracy?
- ¿Qué harías distinto con datos reales y regulación colombiana (SARLAFT)?

---

## 11. Fuera de alcance (para no inflar el proyecto)

- Streaming continuo en tiempo real.
- Model serving en línea / API.
- Deep learning, grafos de redes de fraude.
- Agentes de IA o LLMs (posible proyecto futuro aparte; no mencionarlo como parte de este).
- Más de un dataset.

---

## 12. Reglas técnicas para Claude Code

- PySpark y SQL; nada de pandas sobre el dataset completo (solo para muestras pequeñas o gráficos).
- Notebooks como archivos `.py` con formato de celdas de Databricks (`# COMMAND ----------`), parametrizados con widgets.
- Todo notebook debe ser **idempotente** (re-ejecutable sin duplicar ni romper).
- Nada de rutas `/dbfs` ni `/mnt` (legacy): usar Volumes `/Volumes/fraud_lakehouse/...`.
- Credenciales nunca en el repo; usar variables de entorno o secretos.
- Durante desarrollo trabajar con una muestra (ej. primeras 72 horas) para no gastar la cuota diaria.
- Cada modelo dbt con descripción y tests en su `schema.yml`.
- La app de Streamlit nunca consulta tablas directamente desde las páginas: todo pasa por
  `app/data_access.py`. Las páginas no deben saber si están en modo snapshot o en vivo.
- El snapshot solo contiene tablas agregadas de gold/ops, nunca la tabla completa de transacciones.
- Antes de usar una función o sintaxis de Databricks que no sea básica, verificar en la documentación oficial actual, porque la plataforma cambia nombres con frecuencia.
