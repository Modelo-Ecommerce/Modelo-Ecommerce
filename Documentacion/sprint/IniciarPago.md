# [HU-013] Iniciar proceso de pago

## 📖 Historia de Usuario

**Como** cliente autenticado del sistema,
**Quiero** iniciar el proceso de pago de mi pedido a través de la pasarela Wompi,
**Para** completar mi compra de forma segura usando tarjeta, PSE o Nequi.

---

## 🔁 Flujo Esperado

- El cliente envía los datos del pago al endpoint `POST /api/v1/payments`.
- El sistema valida el token JWT del cliente.
- El sistema verifica que el `orderId` exista y pertenezca al usuario.
- El sistema valida que `amount` sea idéntico al `total` del pedido — regla de dominio: `PaymentAmountMismatchException`.
- El sistema verifica que el pedido no tenga ya un pago en estado `approved` — regla de dominio: `PaymentAlreadyApprovedException`.
- `PaymentService.procesarPago()` envía la solicitud a la API de Wompi con el token del método de pago.
- Wompi retorna un `transactionId` y una `paymentUrl` para redirigir al cliente.
- El sistema registra el pago con `status: "pending"` y retorna la `paymentUrl`.

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST /api/v1/payments`.
- [ ] Se requiere token JWT (rol `client` o `admin`).
- [ ] Se valida que `amount == order.total` — lanza `PaymentAmountMismatchException`.
- [ ] Se valida que el pedido no tenga pago `approved` — lanza `PaymentAlreadyApprovedException`.
- [ ] Se integra con la API de Wompi para procesar el pago.
- [ ] El pago se registra con `status: "pending"` hasta recibir el webhook de confirmación.
- [ ] La respuesta incluye `paymentUrl` para redirigir al cliente al checkout de Wompi.

### 2. 📋 Estructura de la información

- [ ] La respuesta exitosa cumple con la siguiente estructura:

```json
{
  "success": true,
  "statusCode": 201,
  "message": "Pago iniciado. Redirigiendo a pasarela Wompi.",
  "data": {
    "paymentId": 55,
    "orderId": 101,
    "wompiTransactionId": "wompi_txn_98765",
    "status": "pending",
    "amount": 5000000,
    "currency": "COP",
    "paymentUrl": "https://checkout.wompi.co/p/?public-key=...",
    "createdAt": "2026-03-17"
  }
}
```

- [ ] Si el monto no coincide con el total del pedido:

```json
{
  "success": false,
  "statusCode": 422,
  "message": "El monto del pago no coincide con el total del pedido.",
  "error": {
    "error_code": "PAYMENT_AMOUNT_MISMATCH",
    "details": "El monto enviado es $4.000.000 pero el total del pedido es $5.000.000.",
    "timestamp": "2026-03-17"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoint

- **Método HTTP:** `POST`
- **Ruta:** `/api/v1/payments`
- **Autenticación requerida:** 🔐 JWT Requerido (cliente o admin)

### 📥 Request Body

```json
{
  "orderId": 101,
  "userId": 12,
  "amount": 5000000,
  "currency": "COP",
  "paymentMethod": {
    "type": "CARD",
    "token": "tok_test_abc123xyz"
  },
  "customerEmail": "albert@mail.com",
  "redirectUrl": "https://ecommerce.com/orden/101/confirmacion"
}
```

| Campo             | Tipo   | Requerido | Validación                                        |
|-------------------|--------|-----------|---------------------------------------------------|
| `orderId`         | number | ✅        | Pedido debe existir y pertenecer al usuario       |
| `userId`          | number | ✅        | Debe coincidir con el token JWT                   |
| `amount`          | number | ✅        | Debe ser idéntico a `order.total`                 |
| `currency`        | string | ✅        | `"COP"`                                           |
| `paymentMethod`   | object | ✅        | `type`: `"CARD"` \| `"PSE"` \| `"NEQUI"`, `token`: string |
| `customerEmail`   | string | ✅        | Correo para comprobante                           |
| `redirectUrl`     | string | ✅        | URL de redirección tras el pago                   |

### 📤 Response exitosa (201 Created)

```json
{
  "success": true,
  "statusCode": 201,
  "message": "Pago iniciado. Redirigiendo a pasarela Wompi.",
  "data": {
    "paymentId": 55,
    "orderId": 101,
    "wompiTransactionId": "wompi_txn_98765",
    "status": "pending",
    "amount": 5000000,
    "currency": "COP",
    "paymentUrl": "https://checkout.wompi.co/p/?public-key=...",
    "createdAt": "2026-03-17"
  }
}
```

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Pago iniciado exitosamente
- **Precondición:** Pedido `id: 101` existe, `total: 5000000`, `status: "pending"`, token válido.
- **Acción:** `POST /api/v1/payments` con `amount: 5000000`.
- **Resultado esperado:** HTTP `201`, `paymentUrl` presente, pago registrado en `pending`.

### ❌ Caso 2: Monto diferente al total del pedido
- **Acción:** Enviar `amount: 4000000` cuando `order.total: 5000000`.
- **Resultado esperado:** HTTP `422`, `error_code: PAYMENT_AMOUNT_MISMATCH`.

### ❌ Caso 3: Pedido ya tiene pago aprobado
- **Precondición:** Pedido con pago en `status: "approved"`.
- **Resultado esperado:** HTTP `409 Conflict`, `error_code: PAYMENT_ALREADY_APPROVED`.

### ❌ Caso 4: Error en la API de Wompi
- **Precondición:** Wompi retorna error (timeout o rechazo).
- **Resultado esperado:** HTTP `502 Bad Gateway`, mensaje descriptivo del error externo.

### ❌ Caso 5: Pedido no encontrado o no pertenece al usuario
- **Resultado esperado:** HTTP `404` o `403` según corresponda.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional
- [ ] El endpoint inicia el pago correctamente y retorna `201`.
- [ ] Se aplica `PaymentAmountMismatchException` y `PaymentAlreadyApprovedException`.
- [ ] El pago queda registrado con `status: "pending"`.
- [ ] `paymentUrl` de Wompi retornado en la respuesta.

### 🧪 Pruebas Completadas
- [ ] Pruebas unitarias sobre `PaymentService.procesarPago()`.
- [ ] Prueba de `PaymentAmountMismatchException`.
- [ ] Prueba de manejo de error en API de Wompi.

### 📄 Documentación Técnica
- [ ] Endpoint documentado en Swagger / OpenAPI.

### 🔐 Manejo de Errores
- [ ] `422` para monto incorrecto.
- [ ] `409` para pago ya aprobado.
- [ ] `502` para fallo de Wompi.
- [ ] `401` sin token.