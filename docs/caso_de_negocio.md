# Caso de negocio

> Los datos son sintéticos (PaySim) y el banco es ficticio. No se usa información de ningún empleador real.

## La empresa (ficticia)

**Banco Andino Digital**: banco digital con billetera móvil. Opera transferencias, retiros (cash-out), pagos y depósitos.

## El problema

El área de Prevención de Fraude y Cumplimiento (AML) revisa las transacciones de forma manual y con retraso. Ese retraso es lo que aprovecha el atacante en una **toma de cuenta**: transfiere el saldo de la víctima a una cuenta "mula" (`TRANSFER`) y lo retira en efectivo (`CASH_OUT`) antes de que alguien lo note.

Además, el banco debe cumplir con la regulación de prevención de lavado de activos, alineada con las recomendaciones del GAFI/FATF, que exige monitoreo continuo de transacciones y reporte de operaciones sospechosas.

## La restricción operativa

El equipo solo puede revisar un número limitado de alertas por día. Supuesto del proyecto: **50 alertas/día** (por ejemplo, 5 analistas con unas 10 revisiones cada uno).

Un sistema que dispare miles de alertas no sirve. Cada fraude no detectado es dinero perdido, y cada falsa alarma le quita tiempo al analista. El reto no es detectar todo, sino **priorizar bien**: poner primero los casos con riesgo real y descartar los falsos positivos.

## El objetivo

Cada hora llega un lote de transacciones. El objetivo es entregarle al equipo una **cola de alertas priorizada**, que junte reglas AML fáciles de explicar con un score de machine learning, y medir cuánto dinero se salva con eso.

## KPIs del tablero

El tablero debe responder estas preguntas:

1. ¿Cuánto fraude se detectó y cuánto se escapó? (dinero "salvado" vs. perdido)
2. ¿Qué porcentaje del fraude se atrapa (recall) y qué porcentaje de las alertas era fraude real (precisión)?
3. ¿Cuántas alertas se generan por día frente a la capacidad del equipo (50)?
4. ¿Qué tipologías AML generan más alertas?
5. ¿Cuánto tarda el pipeline desde que llega el lote hasta que la alerta está disponible?
6. ¿Están sanos los datos? (filas ingeridas, filas rechazadas, tests pasados y fallidos)

## Supuestos

- `step` (hora 1–743) se convierte a timestamp como `2026-01-01 00:00:00 + step horas`, zona America/Bogota.
- Capacidad de revisión de 50 alertas/día (supuesto propio, no dato real; ejemplo: 5 analistas × 10 revisiones).
