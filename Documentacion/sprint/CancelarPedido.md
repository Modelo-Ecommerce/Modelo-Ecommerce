# [HU-011] Cancelar pedido

## 📖 Historia de Usuario

**Como** cliente autenticado del sistema,
**Quiero** cancelar un pedido que aún no ha sido procesado,
**Para** desistir de la compra y recuperar la disponibilidad de los productos en el inventario.

---

## 🔁 Flujo Esperado

- El cliente envía `DELETE /api/v1/orders/{id}` con el `orderId` en la URL.
- El sistema valida el token JWT y verifica que el pedido pertenece al cliente.
- El sistema verifica que el pedido exista y tenga estado `pending` — regla de dominio: `OrderNotCancellableException` (pedidos `shipped` o `delivered` no pueden cancelarse).
- `OrderService.cancelarPedido()` cambia el estado a `"cancelled"`.
- El sistema llama a `InventoryService` para restaurar el stock de todos los productos del pedido.
- El sistema retorna la confirmación de cancelación con los productos cuyo stock fue restaurado.

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `DELETE /api/v1/orders/{id}`.
- [ ] Se requiere token JWT (rol `client` o `admin`).
- [ ] Solo se puede cancelar si el pedido tiene `status: "pending"` — lanza `OrderNotCancellableException` para cualquier otro estado.
- [ ] El stock de todos los productos del pedido se restaura automáticamente vía `InventoryService`.
- [ ] El cliente solo puede cancelar sus propios pedidos; el admin puede cancelar cualquiera en `pending`.

### 2. 📋 Estructura de la información

- [ ] La respuesta exitosa cumple con la siguiente estructura:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Pedido cancelado correctamente.",
  "data": {
    "orderId": 101,
    "status": "cancelled",
    "cancelledAt": "2026-03-17",
    "stockRestored": [
      {
        "productId": 45,
        "productName": "Laptop Lenovo IdeaPad 3",
        "quantityRestored": 2,
        "currentStock": 17
      }
    ]
  }
}
```

- [ ] Si el pedido no está en `pending`:

```json
{
  "success": false,
  "statusCode": 409,
  "message": "El pedido no puede ser cancelado en su estado actual.",
  "error": {
    "error_code": "ORDER_NOT_CANCELLABLE",
    "details": "Solo los pedidos en estado pending pueden cancelarse. Estado actual: shipped.",
    "timestamp": "2026-03-17"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoint

- **Método HTTP:** `DELETE`
- **Ruta:** `/api/v1/orders/{id}`
- **Autenticación requerida:** 🔐 JWT Requerido (cliente o admin)

### 📥 Request Body

No aplica. El `orderId` se envía como parámetro en la URL.

### 📤 Response exitosa (200 OK)

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Pedido cancelado correctamente.",
  "data": {
    "orderId": 101,
    "status": "cancelled",
    "cancelledAt": "2026-03-17",
    "stockRestored": [
      {
        "productId": 45,
        "productName": "Laptop Lenovo IdeaPad 3",
        "quantityRestored": 2,
        "currentStock": 17
      }
    ]
  }
}
```

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Cancelación exitosa de pedido en `pending`
- **Precondición:** Pedido `id: 101`, `status: "pending"`, pertenece al usuario `id: 12`.
- **Acción:** `DELETE /api/v1/orders/101`.
- **Resultado esperado:** HTTP `200`, `status: "cancelled"`, `stockRestored[]` con los productos restaurados.

### ❌ Caso 2: Pedido en estado `shipped` — no cancelable
- **Precondición:** Pedido `id: 101` tiene `status: "shipped"`.
- **Resultado esperado:** HTTP `409 Conflict`, `error_code: ORDER_NOT_CANCELLABLE`.

### ❌ Caso 3: Pedido en estado `delivered` — no cancelable
- **Precondición:** Pedido `id: 101` tiene `status: "delivered"`.
- **Resultado esperado:** HTTP `409 Conflict`, `error_code: ORDER_NOT_CANCELLABLE`.

### ❌ Caso 4: Cliente intenta cancelar pedido de otro usuario
- **Precondición:** Pedido `id: 101` pertenece al usuario `id: 99`, token del usuario `id: 12`.
- **Resultado esperado:** HTTP `403 Forbidden`, `error_code: FORBIDDEN`.

### ❌ Caso 5: Pedido no encontrado
- **Acción:** `DELETE /api/v1/orders/9999`.
- **Resultado esperado:** HTTP `404 Not Found`, `error_code: ORDER_NOT_FOUND`.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional
- [ ] El endpoint cancela el pedido y retorna `200 OK`.
- [ ] Se aplica `OrderNotCancellableException` para estados diferentes a `pending`.
- [ ] El stock se restaura automáticamente vía `InventoryService`.

### 🧪 Pruebas Completadas
- [ ] Pruebas unitarias sobre `OrderService.cancelarPedido()`.
- [ ] Prueba de `OrderNotCancellableException` para estados `shipped` y `delivered`.
- [ ] Prueba de restauración de stock.

### 📄 Documentación Técnica
- [ ] Endpoint documentado en Swagger / OpenAPI.

### 🔐 Manejo de Errores
- [ ] `409` para pedido no cancelable.
- [ ] `404` para pedido no encontrado.
- [ ] `403` para pedido de otro usuario.
- [ ] `401` sin token.