# [HU-015] Recibir confirmación de pago (Webhook Wompi)

## 📖 Historia de Usuario

**Como** sistema Ecommerce,
**Quiero** recibir notificaciones automáticas de Wompi sobre el resultado de las transacciones,
**Para** actualizar el estado del pago y del pedido, y restaurar el stock si el pago fue rechazado.

---

## 🔁 Flujo Esperado

- Wompi envía automáticamente un `POST /api/v1/payments/webhook` al sistema tras procesar una transacción.
- El sistema valida la firma del webhook para garantizar que la solicitud proviene de Wompi.
- `PaymentService.recibirWebhook()` procesa el evento `transaction.updated`.
- El sistema actualiza el estado del pago vía `PATCH /api/v1/payments/{id}` (uso interno del servicio).
- **Si `status: "APPROVED"`:**
  - El pago pasa a `approved`.
  - El pedido pasa a `status: "processing"`.
- **Si `status: "DECLINED"` o `"VOIDED"`:**
  - El pago pasa a `declined` o `voided`.
  - El pedido pasa a `status: "failed"`.
  - El stock de los productos se restaura automáticamente vía `InventoryService`.
- El sistema **siempre retorna `200 OK`** a Wompi para evitar reintentos automáticos, incluso si ocurre un error interno.

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST /api/v1/payments/webhook`.
- [ ] No requiere token JWT de cliente — es llamado por los servidores de Wompi.
- [ ] Se valida la firma del webhook de Wompi para autenticar la solicitud.
- [ ] Si `status: "APPROVED"`: pago → `approved`, pedido → `processing`.
- [ ] Si `status: "DECLINED"` o `"VOIDED"`: pago → `declined`/`voided`, pedido → `failed`, stock restaurado.
- [ ] El sistema **siempre retorna `200 OK`** a Wompi (incluso ante errores internos) para evitar reintentos.
- [ ] El campo `PATCH /api/v1/payments/{id}` es usado **internamente** por `PaymentService` para actualizar el estado del pago.

### 2. 📋 Estructura de la información

- [ ] Request Body enviado por Wompi:

```json
{
  "event": "transaction.updated",
  "data": {
    "transaction": {
      "id": "wompi_txn_98765",
      "status": "APPROVED",
      "amount_in_cents": 500000000,
      "reference": "101",
      "payment_method_type": "CARD"
    }
  },
  "sent_at": "2026-03-17T12:06:00Z"
}
```

- [ ] Response exitosa (siempre `200 OK`):

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Webhook procesado correctamente.",
  "data": {
    "paymentId": 55,
    "newStatus": "approved",
    "orderId": 101,
    "orderNewStatus": "processing",
    "stockRestored": false
  }
}
```

- [ ] Response para pago rechazado (también `200 OK` hacia Wompi):

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Webhook procesado correctamente.",
  "data": {
    "paymentId": 55,
    "newStatus": "declined",
    "orderId": 101,
    "orderNewStatus": "failed",
    "stockRestored": true
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método  | Ruta                            | Autenticación       | Propósito                              |
|---------|---------------------------------|---------------------|----------------------------------------|
| `POST`  | `/api/v1/payments/webhook`      | 🔓 Wompi Server     | Recibir notificación automática de Wompi |
| `PATCH` | `/api/v1/payments/{id}`         | 🔐 JWT Requerido    | Actualizar estado del pago (uso interno de `PaymentService`) |

### 📥 Request Body — `POST /api/v1/payments/webhook` (enviado por Wompi)

```json
{
  "event": "transaction.updated",
  "data": {
    "transaction": {
      "id": "wompi_txn_98765",
      "status": "APPROVED",
      "amount_in_cents": 500000000,
      "reference": "101",
      "payment_method_type": "CARD"
    }
  },
  "sent_at": "2026-03-17T12:06:00Z"
}
```

| Campo                         | Tipo   | Descripción                                              |
|-------------------------------|--------|----------------------------------------------------------|
| `event`                       | string | Tipo de evento: `"transaction.updated"`                  |
| `data.transaction.id`         | string | `wompiTransactionId` del pago en el sistema              |
| `data.transaction.status`     | string | `"APPROVED"` \| `"DECLINED"` \| `"VOIDED"`              |
| `data.transaction.reference`  | string | `orderId` del pedido relacionado                         |
| `data.transaction.amount_in_cents` | number | Monto en centavos                                   |
| `sent_at`                     | string | Timestamp ISO 8601 del evento                            |

### 📥 Request Body — `PATCH /api/v1/payments/{id}` (uso interno)

```json
{
  "status": "approved"
}
```

| Campo    | Tipo   | Valores válidos                                  |
|----------|--------|--------------------------------------------------|
| `status` | string | `"approved"` \| `"declined"` \| `"voided"`       |

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Webhook con `status: "APPROVED"`
- **Acción:** `POST /api/v1/payments/webhook` con `status: "APPROVED"`.
- **Resultado esperado:** HTTP `200`, pago → `approved`, pedido → `processing`, `stockRestored: false`.

### ✅ Caso 2: Webhook con `status: "DECLINED"`
- **Acción:** `POST /api/v1/payments/webhook` con `status: "DECLINED"`.
- **Resultado esperado:** HTTP `200`, pago → `declined`, pedido → `failed`, stock restaurado, `stockRestored: true`.

### ✅ Caso 3: Error interno al procesar webhook — siempre `200` a Wompi
- **Precondición:** La base de datos no está disponible al recibir el webhook.
- **Resultado esperado:** HTTP `200 OK` a Wompi. Error registrado en logs internos.

### ❌ Caso 4: Firma del webhook inválida
- **Precondición:** El webhook no viene de Wompi (firma incorrecta).
- **Resultado esperado:** HTTP `401 Unauthorized`. No se procesa el evento.

### ✅ Caso 5: PATCH interno actualiza estado del pago
- **Acción:** `PATCH /api/v1/payments/55` con `status: "approved"` (llamado por `PaymentService`).
- **Resultado esperado:** HTTP `200`, estado del pago actualizado correctamente.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional
- [ ] El webhook procesa correctamente `APPROVED`, `DECLINED` y `VOIDED`.
- [ ] El stock se restaura automáticamente para pagos `DECLINED`/`VOIDED`.
- [ ] El sistema siempre retorna `200 OK` a Wompi.
- [ ] La firma del webhook se valida para garantizar autenticidad.

### 🧪 Pruebas Completadas
- [ ] Pruebas unitarias sobre `PaymentService.recibirWebhook()`.
- [ ] Prueba de restauración de stock en pago rechazado.
- [ ] Prueba de resiliencia: error interno no interrumpe respuesta a Wompi.

### 📄 Documentación Técnica
- [ ] Endpoint de webhook documentado en Swagger / OpenAPI como endpoint externo de Wompi.
- [ ] `PATCH /api/v1/payments/{id}` documentado como uso interno de `PaymentService`.

### 🔐 Manejo de Errores
- [ ] `401` si la firma del webhook no es válida.
- [ ] Errores internos → log, nunca expuesto a Wompi.
- [ ] `200 OK` siempre hacia Wompi para evitar reintentos.