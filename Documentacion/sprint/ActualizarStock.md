# [HU-017] Actualizar stock de producto

## 📖 Historia de Usuario

**Como** administrador autenticado del sistema,
**Quiero** aumentar o disminuir el stock de un producto en el inventario,
**Para** reflejar entradas por reabastecimiento, devoluciones o ajustes manuales sin necesidad de crear un pedido.

---

## 🔁 Flujo Esperado

- El administrador envía el `productId` como parámetro en la URL al endpoint `PATCH /api/v1/inventory/{productId}` junto con el body de operación.
- El sistema valida el token JWT y verifica que el rol sea `admin`.
- El sistema verifica que el `productId` exista en la tabla `products`.
- El sistema verifica que la operación `decrease` no deje el stock en negativo (regla de dominio: `InsufficientStockException`).
- El sistema registra el movimiento en la tabla `inventory_movements` con `reason` y `orderId` obligatorios si el motivo es `purchase` (regla de dominio: `InventoryMovement`).
- El sistema actualiza el campo `currentStock` en la tabla `inventory`.
- Si el stock resultante es menor o igual a 5, se activa automáticamente la notificación de stock bajo.
- El sistema retorna el estado del inventario antes y después de la operación.

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `PATCH /api/v1/inventory/{productId}`.
- [ ] Se requiere token JWT con rol `admin`.
- [ ] Se valida que `operation` sea `"increase"` o `"decrease"`.
- [ ] Para operación `decrease`: se verifica que `currentStock - quantity >= 0` (regla de dominio: `InsufficientStockException`).
- [ ] Se registra el movimiento en `inventory_movements` con `reason` y `orderId` (obligatorio si `reason = "purchase"`).
- [ ] Si `currentStock` resultante `<= LOW_STOCK_THRESHOLD` (5), se invoca `InventoryService.notificarStockBajo()`.
- [ ] Se usa `IInventoryRepository.updateStock()` y `IInventoryRepository.registerMovement()`.

### 2. 📆 Estructura de la información

- [ ] La respuesta exitosa cumple con la siguiente estructura:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Stock actualizado correctamente.",
  "data": {
    "productId": 45,
    "productName": "Laptop Lenovo IdeaPad 3",
    "previousStock": 15,
    "quantityChanged": 2,
    "currentStock": 13,
    "isLowStock": false,
    "updatedAt": "2026-03-17"
  }
}
```

- [ ] Si el stock resultante sería negativo, el sistema retorna:

```json
{
  "success": false,
  "statusCode": 422,
  "message": "Stock insuficiente para realizar la operación.",
  "error": {
    "error_code": "INSUFFICIENT_STOCK",
    "details": "El stock actual es 2 y se intentó descontar 5 unidades. El stock no puede ser negativo.",
    "timestamp": "2026-03-17"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoint

- **Método HTTP:** `PATCH`
- **Ruta:** `/api/v1/inventory/{productId}`
- **Autenticación requerida:** ✅ Sí (JWT Bearer Token — rol `admin`)

### 📥 Request Body

```json
{
  "operation": "decrease",
  "quantity": 2,
  "reason": "purchase",
  "orderId": 101
}
```

| Campo       | Tipo   | Requerido | Validación                                              |
|-------------|--------|-----------|---------------------------------------------------------|
| `operation` | string | ✅        | `"increase"` o `"decrease"`                             |
| `quantity`  | number | ✅        | Mayor a 0                                               |
| `reason`    | string | ✅        | `"purchase"`, `"return"` o `"restock"`                  |
| `orderId`   | number | ⚠️ Condicional | Obligatorio si `reason = "purchase"` (regla dominio) |

### 📤 Response exitosa (200 OK)

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Stock actualizado correctamente.",
  "data": {
    "productId": 45,
    "productName": "Laptop Lenovo IdeaPad 3",
    "previousStock": 15,
    "quantityChanged": 2,
    "currentStock": 13,
    "isLowStock": false,
    "updatedAt": "2026-03-17"
  }
}
```

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Disminución de stock exitosa (purchase)

- **Precondición:** El producto con `id: 45` tiene `currentStock: 15`.
- **Acción:** Ejecutar `PATCH /api/v1/inventory/45` con `operation: "decrease"`, `quantity: 2`, `reason: "purchase"`, `orderId: 101`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - `previousStock: 15`, `currentStock: 13`, `isLowStock: false`
  - Movimiento registrado en `inventory_movements`

### ✅ Caso 2: Aumento de stock por reabastecimiento

- **Precondición:** El producto con `id: 45` tiene `currentStock: 3`.
- **Acción:** Ejecutar `PATCH /api/v1/inventory/45` con `operation: "increase"`, `quantity: 10`, `reason: "restock"`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - `previousStock: 3`, `currentStock: 13`, `isLowStock: false`

### ✅ Caso 3: Disminución que activa alerta de stock bajo

- **Precondición:** El producto tiene `currentStock: 7`.
- **Acción:** Ejecutar `PATCH /api/v1/inventory/45` con `operation: "decrease"`, `quantity: 3`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - `currentStock: 4`, `isLowStock: true`
  - Se invoca `notificarStockBajo()` automáticamente

### ❌ Caso 4: Stock resultante negativo

- **Precondición:** El producto tiene `currentStock: 2`.
- **Acción:** Ejecutar `PATCH /api/v1/inventory/45` con `operation: "decrease"`, `quantity: 5`.
- **Resultado esperado:**
  - Código HTTP `422 Unprocessable Entity`
  - `error_code`: `INSUFFICIENT_STOCK`

### ❌ Caso 5: `reason: "purchase"` sin `orderId`

- **Precondición:** Ninguna.
- **Acción:** Enviar `reason: "purchase"` sin campo `orderId`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - `error_code`: `VALIDATION_ERROR`
  - Mensaje: `"El campo orderId es obligatorio cuando reason es purchase."`

### ❌ Caso 6: Producto no encontrado

- **Precondición:** El `productId` no existe.
- **Acción:** Ejecutar `PATCH /api/v1/inventory/9999`.
- **Resultado esperado:**
  - Código HTTP `404 Not Found`
  - `error_code`: `PRODUCT_NOT_FOUND`

### ❌ Caso 7: Token con rol `client`

- **Precondición:** Token válido con rol `client`.
- **Acción:** Ejecutar `PATCH /api/v1/inventory/45`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`
  - `error_code`: `FORBIDDEN`

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El endpoint actualiza correctamente el stock según la operación indicada.
- [ ] Se aplica la regla de dominio `InsufficientStockException` (stock nunca negativo).
- [ ] Se registra el movimiento en `inventory_movements` con `reason` y `orderId`.
- [ ] Se invoca `notificarStockBajo()` cuando `currentStock <= 5`.
- [ ] Solo usuarios con rol `admin` pueden acceder al endpoint.

### 🧪 Pruebas Completadas

- [ ] Pruebas unitarias sobre `InventoryService.reducirStock()` y `InventoryService.aumentarStock()`.
- [ ] Prueba de regla de dominio: stock negativo.
- [ ] Prueba de activación de alerta de stock bajo.
- [ ] Prueba de validación condicional de `orderId`.

### 📄 Documentación Técnica

- [ ] Endpoint documentado en Swagger / OpenAPI.
- [ ] Se describe: propósito, campos de entrada, validaciones condicionales, respuesta y errores.

### 🔐 Manejo de Errores

- [ ] Código `422` para stock insuficiente.
- [ ] Código `400` para validaciones de campos (falta `orderId` con `reason=purchase`).
- [ ] Código `404` para producto no encontrado.
- [ ] Código `403` para rol no autorizado.
- [ ] Código `401` sin token.
- [ ] Código `503` si la base de datos no está disponible.
