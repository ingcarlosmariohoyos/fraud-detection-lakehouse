# Databricks notebook source
# MAGIC %md
# MAGIC # 00 — Setup del catálogo
# MAGIC Crea el catálogo `fraud_lakehouse`, sus esquemas y los Volumes de `landing`. Idempotente.

# COMMAND ----------

# Parámetro: nombre del catálogo (se puede cambiar desde la cajita de arriba)
dbutils.widgets.text("catalog_name", "fraud_lakehouse", "Nombre del catálogo")
catalog = dbutils.widgets.get("catalog_name")

print(f"Catálogo: {catalog}")

# COMMAND ----------

# Esquemas del proyecto: una etapa del pipeline por esquema
schemas = ["landing", "bronze", "silver", "gold", "ml", "ops"]

# Volumes de landing: por donde pasan los archivos CSV
landing_volumes = ["source_full", "source_by_hour", "incoming"]

print(f"Esquemas: {schemas}")
print(f"Volumes en landing: {landing_volumes}")

# COMMAND ----------

# Crear el catálogo solo si no existe (así el notebook es idempotente)
spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")

display(spark.sql("SHOW CATALOGS"))

# COMMAND ----------

# Crear los esquemas: un bucle recorre la lista y crea cada uno si no existe
for schema in schemas:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")

display(spark.sql(f"SHOW SCHEMAS IN {catalog}"))

# COMMAND ----------

# Crear los Volumes de landing (managed volumes: Unity Catalog administra el almacenamiento)
for volume in landing_volumes:
    spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalog}.landing.{volume}")

display(spark.sql(f"SHOW VOLUMES IN {catalog}.landing"))
