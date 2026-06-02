# [HU-012] Actualizar estado del pedido

## 📖 Historia de Usuario

**Como** administrador autenticado del sistema,
**Quiero** actualizar el estado de un pedido a medida que avanza en el proceso de despacho,
**Para** mantener informado al cliente sobre el progreso de su compra.

---

## 🔁 Flujo Esperado

- El administrador envía el nuevo estado al endpoint `PATCH /api/v1/orders/{id}`.
- El sistema valida el token JWT y verifica que el rol sea `admin`.
- El sistema verifica que el pedido exista.
- El sistema valida que la transición de estado sea válida según el flujo permitido:
  `pending` → `processing` → `shipped` → `delivered`
- El sistema actualiza el estado y retorna el resultado con el estado anterior y el nuevo.

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `PATCH /api/v1/orders/{id}`.
- [ ] Se requiere token JWT con rol `admin`.
- [ ] Solo se permiten las transiciones válidas: `pending→processing`, `processing→shipped`, `shipped→delivered`.
- [ ] Cualquier otra transición retorna `400 Bad Request`.
- [ ] No se puede actualizar un pedido en estado `cancelled` o `failed`.

### 2. 📋 Estructura de la información

- [ ] La respuesta exitosa cumple con la siguiente estructura:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Estado del pedido actualizado correctamente.",
  "data": {
    "orderId": 101,
    "previousStatus": "processing",
    "newStatus": "shipped",
    "updatedAt": "2026-03-17"
  }
}
```

- [ ] Si la transición no es válida:

```json
{
  "success": false,
  "statusCode": 400,
  "message": "Transición de estado no permitida.",
  "error": {
    "error_code": "INVALID_STATUS_TRANSITION",
    "details": "No se puede cambiar de pending a delivered. Transiciones válidas: pending → processing → shipped → delivered.",
    "timestamp": "2026-03-17"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoint

- **Método HTTP:** `PATCH`
- **Ruta:** `/api/v1/orders/{id}`
- **Autenticación requerida:** 🛡️ Solo Admin (JWT con rol `admin`)

### 📥 Request Body

```json
{
  "status": "shipped"
}
```

| Campo    | Tipo   | Requerido | Validación                                                        |
|----------|--------|-----------|-------------------------------------------------------------------|
| `status` | string | ✅        | Valores válidos: `"processing"` \| `"shipped"` \| `"delivered"`   |

### 📤 Response exitosa (200 OK)

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Estado del pedido actualizado correctamente.",
  "data": {
    "orderId": 101,
    "previousStatus": "processing",
    "newStatus": "shipped",
    "updatedAt": "2026-03-17"
  }
}
```

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Transición válida `pending → processing`
- **Precondición:** Pedido `id: 101` tiene `status: "pending"`, token admin.
- **Acción:** `PATCH /api/v1/orders/101` con `status: "processing"`.
- **Resultado esperado:** HTTP `200`, `previousStatus: "pending"`, `newStatus: "processing"`.

### ✅ Caso 2: Transición válida `processing → shipped`
- **Precondición:** Pedido con `status: "processing"`.
- **Resultado esperado:** HTTP `200`, `newStatus: "shipped"`.

### ✅ Caso 3: Transición válida `shipped → delivered`
- **Precondición:** Pedido con `status: "shipped"`.
- **Resultado esperado:** HTTP `200`, `newStatus: "delivered"`.

### ❌ Caso 4: Transición inválida (saltar estados)
- **Acción:** `PATCH /api/v1/orders/101` con `status: "delivered"` estando en `pending`.
- **Resultado esperado:** HTTP `400 Bad Request`, `error_code: INVALID_STATUS_TRANSITION`.

### ❌ Caso 5: Intentar actualizar pedido `cancelled`
- **Precondición:** Pedido tiene `status: "cancelled"`.
- **Resultado esperado:** HTTP `409 Conflict`, `error_code: ORDER_NOT_UPDATABLE`.

### ❌ Caso 6: Token con rol `client`
- **Resultado esperado:** HTTP `403 Forbidden`, `error_code: FORBIDDEN`.

### ❌ Caso 7: Pedido no encontrado
- **Acción:** `PATCH /api/v1/orders/9999`.
- **Resultado esperado:** HTTP `404 Not Found`, `error_code: ORDER_NOT_FOUND`.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional
- [ ] Solo el admin puede actualizar el estado.
- [ ] Las transiciones están controladas correctamente.
- [ ] Se retorna `previousStatus` y `newStatus` en la respuesta.

### 🧪 Pruebas Completadas
- [ ] Pruebas unitarias sobre `OrderService.actualizarEstado()`.
- [ ] Prueba de todas las transiciones válidas e inválidas.

### 📄 Documentación Técnica
- [ ] Endpoint documentado en Swagger / OpenAPI con los estados válidos.

### 🔐 Manejo de Errores
- [ ] `400` para transición inválida.
- [ ] `409` para pedido no actualizable.
- [ ] `404` para pedido no encontrado.
- [ ] `403` para rol no autorizado.