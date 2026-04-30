# [HU-007] Agregar producto al carrito

## 📖 Historia de Usuario

**Como** cliente autenticado del sistema,
**Quiero** agregar productos al carrito de compras indicando la cantidad deseada,
**Para** seleccionar los artículos que deseo comprar antes de confirmar el pedido.

---

## 🔁 Flujo Esperado

- El cliente envía los datos del producto a agregar al endpoint `POST /api/v1/carts/items`.
- El sistema valida el token JWT del cliente.
- El sistema verifica que el `productId` exista y tenga estado `active` (regla de dominio: productos `discontinued` no pueden agregarse).
- El sistema consulta `InventoryService` (`GET /api/v1/inventory/{productId}`) para verificar stock disponible antes de agregar.
- Si el producto ya existe en el carrito, el sistema suma la cantidad al ítem existente (regla de dominio: no se duplican ítems).
- El sistema verifica que el total de ítems en el carrito no supere `MAX_ITEMS_PER_CART` (20).
- El sistema actualiza el carrito y retorna el estado actual con el total recalculado.

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST /api/v1/carts/items`.
- [ ] Se requiere token JWT (rol `client` o `admin`).
- [ ] Se valida que `productId` exista y tenga estado `active`.
- [ ] Se consulta `InventoryService` para verificar stock antes de agregar (`CartService` → `InventoryService`).
- [ ] Si el producto ya existe en el carrito, la cantidad se suma al ítem existente (no se crea un ítem duplicado).
- [ ] La cantidad agregada no puede superar el stock disponible.
- [ ] El total de ítems distintos en el carrito no supera `MAX_ITEMS_PER_CART` (20).

### 2. 📋 Estructura de la información

- [ ] La respuesta exitosa cumple con la siguiente estructura:

```json
{
  "success": true,
  "statusCode": 201,
  "message": "Producto agregado al carrito.",
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
    "total": 5000000
  }
}
```

- [ ] Si el stock es insuficiente:

```json
{
  "success": false,
  "statusCode": 422,
  "message": "Stock insuficiente para agregar el producto al carrito.",
  "error": {
    "error_code": "INSUFFICIENT_STOCK",
    "details": "El producto Laptop Lenovo IdeaPad 3 solo tiene 1 unidad disponible.",
    "timestamp": "2026-03-17"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoint

- **Método HTTP:** `POST`
- **Ruta:** `/api/v1/carts/items`
- **Autenticación requerida:** 🔐 JWT Requerido (cliente o admin)

### 📥 Request Body

```json
{
  "userId": 12,
  "productId": 45,
  "quantity": 2
}
```

| Campo       | Tipo   | Requerido | Validación                                              |
|-------------|--------|-----------|---------------------------------------------------------|
| `userId`    | number | ✅        | Debe coincidir con el usuario del token JWT             |
| `productId` | number | ✅        | Debe existir y tener estado `active`                    |
| `quantity`  | number | ✅        | Mínimo 1 unidad, no puede superar el stock disponible  |

### 📤 Response exitosa (201 Created)

```json
{
  "success": true,
  "statusCode": 201,
  "message": "Producto agregado al carrito.",
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
    "total": 5000000
  }
}
```

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Agregar producto nuevo al carrito exitosamente
- **Precondición:** Producto `id: 45` existe (`active`), stock disponible ≥ 2, token válido.
- **Acción:** `POST /api/v1/carts/items` con `userId: 12`, `productId: 45`, `quantity: 2`.
- **Resultado esperado:** HTTP `201 Created`, ítem en `items[]`, `total` recalculado.

### ✅ Caso 2: Agregar el mismo producto — suma cantidad al ítem existente
- **Precondición:** Producto `id: 45` ya está en el carrito con `quantity: 1`.
- **Acción:** `POST /api/v1/carts/items` con `productId: 45`, `quantity: 1`.
- **Resultado esperado:** HTTP `201`, ítem existente actualizado a `quantity: 2`, no se crea ítem duplicado.

### ❌ Caso 3: Stock insuficiente
- **Precondición:** Producto `id: 45` tiene `stock: 1`.
- **Acción:** Enviar `quantity: 3`.
- **Resultado esperado:** HTTP `422`, `error_code: INSUFFICIENT_STOCK`.

### ❌ Caso 4: Producto con estado `discontinued`
- **Precondición:** Producto `id: 45` tiene `status: "discontinued"`.
- **Resultado esperado:** HTTP `422`, `error_code: PRODUCT_DISCONTINUED`.

### ❌ Caso 5: Límite de ítems distintos superado (`MAX_ITEMS_PER_CART`)
- **Precondición:** El carrito ya tiene 20 ítems distintos.
- **Resultado esperado:** HTTP `422`, `error_code: CART_ITEM_LIMIT_EXCEEDED`.

### ❌ Caso 6: `userId` no coincide con el token
- **Acción:** Enviar `userId: 99` con token del usuario `id: 12`.
- **Resultado esperado:** HTTP `403 Forbidden`, `error_code: FORBIDDEN`.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional
- [ ] El endpoint agrega el producto al carrito correctamente.
- [ ] Se consulta `InventoryService` para verificar stock antes de agregar.
- [ ] No se crean ítems duplicados — se suma la cantidad al existente.
- [ ] Se respeta el límite `MAX_ITEMS_PER_CART` (20).

### 🧪 Pruebas Completadas
- [ ] Pruebas unitarias sobre `CartService.agregarItem()`.
- [ ] Prueba de suma de cantidad en ítem existente.
- [ ] Prueba de stock insuficiente y producto descontinuado.

### 📄 Documentación Técnica
- [ ] Endpoint documentado en Swagger / OpenAPI.

### 🔐 Manejo de Errores
- [ ] `422` para stock insuficiente, producto descontinuado, límite de carrito.
- [ ] `403` si `userId` no coincide con el token.
- [ ] `401` sin token.