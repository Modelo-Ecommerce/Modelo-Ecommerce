# [HU-008] Consultar y confirmar carrito

## 📖 Historia de Usuario

**Como** cliente autenticado del sistema,
**Quiero** consultar el contenido de mi carrito y poder gestionar los ítems (actualizar cantidades o eliminar productos),
**Para** revisar mi selección antes de crear el pedido y asegurarme de que todo esté correcto.

---

## 🔁 Flujo Esperado

**Consultar carrito:**
- El cliente solicita su carrito con `GET /api/v1/carts/{userId}`.
- El sistema retorna todos los ítems del carrito con subtotales y el total general.
- El sistema indica si el carrito cumple con `MIN_CART_QUANTITY` (mínimo 3 unidades totales) para poder confirmar.

**Actualizar cantidad de ítem:**
- El cliente envía la nueva cantidad al endpoint `PATCH /api/v1/carts/items/{id}`.
- El sistema verifica que la nueva cantidad no supere el stock disponible.
- El sistema recalcula `subtotal` y `total` del carrito.

**Eliminar ítem del carrito:**
- El cliente envía `DELETE /api/v1/carts/items/{id}` para quitar un producto del carrito.
- El sistema actualiza el total del carrito.

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone `GET /api/v1/carts/{userId}` — JWT requerido.
- [ ] Se expone `PATCH /api/v1/carts/items/{id}` — JWT requerido.
- [ ] Se expone `DELETE /api/v1/carts/items/{id}` — JWT requerido.
- [ ] `PATCH`: la `quantity` enviada es la **cantidad total** del ítem (no el delta a sumar).
- [ ] `PATCH`: se verifica stock disponible antes de actualizar.
- [ ] La respuesta incluye `itemCount` y si el total de unidades cumple `MIN_CART_QUANTITY` (3).
- [ ] El campo `vaciarCarrito()` se ejecuta automáticamente al confirmar el pedido (vía `OrderService`).

### 2. 📋 Estructura de la información

- [ ] Response exitosa de `GET /api/v1/carts/{userId}`:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Carrito obtenido correctamente.",
  "data": {
    "cartId": 7,
    "userId": 12,
    "items": [
      {
        "itemId": 33,
        "productId": 45,
        "productName": "Laptop Lenovo IdeaPad 3",
        "unitPrice": 2500000,
        "quantity": 2,
        "subtotal": 5000000
      }
    ],
    "itemCount": 2,
    "total": 5000000
  }
}
```

- [ ] Response exitosa de `PATCH /api/v1/carts/items/{id}`:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Cantidad actualizada correctamente.",
  "data": {
    "cartId": 7,
    "userId": 12,
    "items": [...],
    "itemCount": 3,
    "total": 7500000
  }
}
```

- [ ] Response exitosa de `DELETE /api/v1/carts/items/{id}`:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Ítem eliminado del carrito.",
  "data": {
    "cartId": 7,
    "userId": 12,
    "items": [...],
    "itemCount": 1,
    "total": 2500000
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método   | Ruta                          | Autenticación     | Propósito                    |
|----------|-------------------------------|-------------------|------------------------------|
| `GET`    | `/api/v1/carts/{userId}`      | 🔐 JWT Requerido  | Consultar / confirmar carrito |
| `PATCH`  | `/api/v1/carts/items/{id}`    | 🔐 JWT Requerido  | Actualizar cantidad de ítem  |
| `DELETE` | `/api/v1/carts/items/{id}`    | 🔐 JWT Requerido  | Eliminar ítem del carrito    |

### 📥 Request Body — `PATCH /api/v1/carts/items/{id}`

```json
{
  "quantity": 3
}
```

| Campo      | Tipo   | Requerido | Validación                                                    |
|------------|--------|-----------|---------------------------------------------------------------|
| `quantity` | number | ✅        | Nueva cantidad total del ítem (no el delta). Mínimo 1 unidad. |

> `GET` y `DELETE`: No requieren body — los parámetros van en la URL.

> **Regla de negocio para confirmar:** El total de unidades en el carrito debe ser ≥ `MIN_CART_QUANTITY` (3) antes de proceder a `POST /api/v1/orders`. Si no cumple, `OrderService` lanza `MinimumQuantityException`.

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Consulta exitosa del carrito
- **Precondición:** Usuario `id: 12` tiene carrito con ítems.
- **Acción:** `GET /api/v1/carts/12`.
- **Resultado esperado:** HTTP `200`, lista de ítems con `subtotal` y `total` correctos.

### ✅ Caso 2: Actualización de cantidad exitosa
- **Precondición:** Ítem `id: 33` existe, stock disponible ≥ 3.
- **Acción:** `PATCH /api/v1/carts/items/33` con `quantity: 3`.
- **Resultado esperado:** HTTP `200`, `subtotal` e `itemCount` recalculados.

### ✅ Caso 3: Eliminación de ítem exitosa
- **Acción:** `DELETE /api/v1/carts/items/33`.
- **Resultado esperado:** HTTP `200`, ítem eliminado, `total` recalculado.

### ❌ Caso 4: PATCH con cantidad que supera el stock
- **Precondición:** Producto tiene `stock: 2`.
- **Acción:** `PATCH /api/v1/carts/items/33` con `quantity: 5`.
- **Resultado esperado:** HTTP `422`, `error_code: INSUFFICIENT_STOCK`.

### ❌ Caso 5: Carrito no encontrado
- **Acción:** `GET /api/v1/carts/9999`.
- **Resultado esperado:** HTTP `404`, `error_code: CART_NOT_FOUND`.

### ❌ Caso 6: Token inválido o sin autenticación
- **Resultado esperado:** HTTP `401 Unauthorized`.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional
- [ ] Los tres endpoints funcionan correctamente.
- [ ] `PATCH` recalcula `subtotal` y `total` correctamente.
- [ ] `vaciarCarrito()` se invoca automáticamente al crear el pedido.

### 🧪 Pruebas Completadas
- [ ] Pruebas unitarias sobre `CartService.actualizarCantidad()` y `CartService.vaciarCarrito()`.
- [ ] Prueba de PATCH con cantidad que supera stock.

### 📄 Documentación Técnica
- [ ] Los tres endpoints documentados en Swagger / OpenAPI.

### 🔐 Manejo de Errores
- [ ] `422` para stock insuficiente en PATCH.
- [ ] `404` para carrito o ítem no encontrado.
- [ ] `401` sin token.