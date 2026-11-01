# Databricks notebook source
# MAGIC %md
# MAGIC # 00 — Setup del catálogo
# MAGIC Crea el catálogo `fraud_lakehouse`, sus esquemas y los Volumes de `landing`. Idempotente.

# COMMAND ----------

# Parámetro: nombre del catálogo (se puede cambiar desde la cajita de arriba)
dbutils.widgets.text("catalog_name", "fraud_lakehouse", "Nombre del catálogo")
catalog = dbutils.widgets.get("catalog_name")

print(f"Catálogo: {catalog}")
