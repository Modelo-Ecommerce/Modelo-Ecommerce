# [HU-014] Consultar estado del pago

## 📖 Historia de Usuario

**Como** cliente o administrador autenticado,
**Quiero** consultar el estado actual de un pago por su ID,
**Para** saber si mi transacción fue aprobada, rechazada o sigue pendiente.

---

## 🔁 Flujo Esperado

- El usuario envía el `paymentId` como parámetro en la URL a `GET /api/v1/payments/{id}`.
- El sistema valida el token JWT.
- El sistema verifica que el pago exista.
- Si el usuario tiene rol `client`, solo puede consultar pagos asociados a sus propios pedidos.
- Si el usuario tiene rol `admin`, puede consultar cualquier pago.
- El sistema retorna los datos completos del pago incluyendo `wompiTransactionId`, `status`, `approvedAt` si aplica.

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `GET /api/v1/payments/{id}`.
- [ ] Se requiere token JWT (rol `client` o `admin`).
- [ ] Cliente: solo puede ver pagos de sus propios pedidos. Admin: puede ver cualquiera.
- [ ] Se retorna `approvedAt` solo si el estado es `approved`.
- [ ] Los estados posibles son: `pending` | `approved` | `declined` | `voided`.

### 2. 📋 Estructura de la información

- [ ] La respuesta exitosa cumple con la siguiente estructura:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Pago encontrado.",
  "data": {
    "paymentId": 55,
    "orderId": 101,
    "wompiTransactionId": "wompi_txn_98765",
    "status": "approved",
    "amount": 5000000,
    "currency": "COP",
    "paymentMethodType": "CARD",
    "createdAt": "2026-03-17",
    "approvedAt": "2026-03-17T12:06:00Z"
  }
}
```

- [ ] Si el pago no existe:

```json
{
  "success": false,
  "statusCode": 404,
  "message": "Pago no encontrado.",
  "error": {
    "error_code": "PAYMENT_NOT_FOUND",
    "details": "El pago con id 55 no existe en el sistema.",
    "timestamp": "2026-03-17"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoint

- **Método HTTP:** `GET`
- **Ruta:** `/api/v1/payments/{id}`
- **Autenticación requerida:** 🔐 JWT Requerido (cliente o admin)

### 📥 Request Body

No aplica. El `paymentId` se envía como parámetro en la URL.

### 📤 Response exitosa (200 OK)

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Pago encontrado.",
  "data": {
    "paymentId": 55,
    "orderId": 101,
    "wompiTransactionId": "wompi_txn_98765",
    "status": "approved",
    "amount": 5000000,
    "currency": "COP",
    "paymentMethodType": "CARD",
    "createdAt": "2026-03-17",
    "approvedAt": "2026-03-17T12:06:00Z"
  }
}
```

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Consulta exitosa de pago aprobado
- **Precondición:** Pago `id: 55` existe con `status: "approved"`.
- **Acción:** `GET /api/v1/payments/55`.
- **Resultado esperado:** HTTP `200`, campo `approvedAt` presente.

### ✅ Caso 2: Consulta de pago pendiente
- **Precondición:** Pago `id: 55` con `status: "pending"`.
- **Resultado esperado:** HTTP `200`, `approvedAt` ausente o `null`.

### ✅ Caso 3: Admin consulta pago de cualquier usuario
- **Precondición:** Token con rol `admin`.
- **Resultado esperado:** HTTP `200`, datos completos del pago.

### ❌ Caso 4: Cliente intenta ver pago de otro usuario
- **Precondición:** Pago asociado a pedido de otro usuario.
- **Resultado esperado:** HTTP `403 Forbidden`, `error_code: FORBIDDEN`.

### ❌ Caso 5: Pago no encontrado
- **Acción:** `GET /api/v1/payments/9999`.
- **Resultado esperado:** HTTP `404 Not Found`, `error_code: PAYMENT_NOT_FOUND`.

### ❌ Caso 6: Sin token de autenticación
- **Resultado esperado:** HTTP `401 Unauthorized`.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional
- [ ] El endpoint retorna los datos completos del pago con `200 OK`.
- [ ] Se restringe el acceso del cliente a sus propios pagos.
- [ ] `approvedAt` solo aparece cuando `status: "approved"`.

### 🧪 Pruebas Completadas
- [ ] Pruebas unitarias sobre `PaymentService` y consulta por ID.
- [ ] Prueba de restricción de acceso cliente vs admin.

### 📄 Documentación Técnica
- [ ] Endpoint documentado en Swagger / OpenAPI.

### 🔐 Manejo de Errores
- [ ] `404` si el pago no existe.
- [ ] `403` si el cliente consulta pago ajeno.
- [ ] `401` sin token.