# [HU-009] Crear pedido

## 📖 Historia de Usuario

**Como** cliente autenticado del sistema,
**Quiero** crear un pedido a partir del contenido de mi carrito indicando la dirección de envío y método de pago,
**Para** formalizar mi compra e iniciar el proceso de pago.

---

## 🔁 Flujo Esperado

- El cliente envía los datos del pedido al endpoint `POST /api/v1/orders`.
- El sistema valida el token JWT del cliente.
- El sistema valida que el total del carrito sea mayor o igual a `MIN_ORDER_AMOUNT` ($60.000 COP) — regla de dominio: `MinimumOrderAmountException`.
- El sistema valida que el total de unidades en el carrito sea ≥ `MIN_CART_QUANTITY` (3) — regla de dominio: `MinimumQuantityException`.
- `OrderService` orquesta la transacción completa:
  1. Verifica stock de todos los productos del carrito vía `InventoryService`.
  2. Descuenta el inventario vía `InventoryService.reducirStock()`.
  3. Crea el pedido con `status: "pending"`.
  4. Vacía el carrito vía `CartService.vaciarCarrito()`.
  5. Inicia el pago vía `PaymentService.procesarPago()` → retorna `paymentUrl`.
- Si cualquier paso falla, la transacción se revierte: el stock se restaura y el pedido queda en `status: "failed"`.

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST /api/v1/orders`.
- [ ] Se requiere token JWT (rol `client` o `admin`).
- [ ] Se valida que el total ≥ `MIN_ORDER_AMOUNT` ($60.000 COP) — lanza `MinimumOrderAmountException`.
- [ ] Se valida que el total de unidades ≥ `MIN_CART_QUANTITY` (3) — lanza `MinimumQuantityException`.
- [ ] La transacción es atómica: si falla el pago, el stock se revierte y el pedido queda en `"failed"`.
- [ ] El carrito se vacía automáticamente al crear el pedido exitosamente.
- [ ] La respuesta incluye `paymentUrl` para redirigir al cliente a Wompi.

### 2. 📋 Estructura de la información

- [ ] La respuesta exitosa cumple con la siguiente estructura:

```json
{
  "success": true,
  "statusCode": 201,
  "message": "Pedido creado correctamente.",
  "data": {
    "orderId": 101,
    "userId": 12,
    "status": "pending",
    "total": 5000000,
    "paymentUrl": "https://checkout.wompi.co/p/?public-key=...",
    "createdAt": "2026-03-17",
    "items": [
      {
        "productId": 45,
        "productName": "Laptop Lenovo IdeaPad 3",
        "quantity": 2,
        "unitPrice": 2500000,
        "subtotal": 5000000
      }
    ]
  }
}
```

- [ ] Si el total es menor al mínimo:

```json
{
  "success": false,
  "statusCode": 422,
  "message": "El valor del pedido no cumple el mínimo requerido.",
  "error": {
    "error_code": "MINIMUM_ORDER_AMOUNT",
    "details": "El valor mínimo de un pedido es $60.000 COP (MIN_ORDER_AMOUNT).",
    "timestamp": "2026-03-17"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoint

- **Método HTTP:** `POST`
- **Ruta:** `/api/v1/orders`
- **Autenticación requerida:** 🔐 JWT Requerido (cliente o admin)

### 📥 Request Body

```json
{
  "userId": 12,
  "cartId": 7,
  "shippingAddress": {
    "street": "Cra 15 #30-12",
    "city": "Bucaramanga",
    "department": "Santander",
    "postalCode": "680001"
  },
  "paymentMethod": "wompi_card"
}
```

| Campo             | Tipo   | Requerido | Validación                                              |
|-------------------|--------|-----------|---------------------------------------------------------|
| `userId`          | number | ✅        | Debe coincidir con el usuario del token JWT             |
| `cartId`          | number | ✅        | Carrito debe existir y pertenecer al `userId`           |
| `shippingAddress` | object | ✅        | Campos: `street`, `city`, `department`, `postalCode`    |
| `paymentMethod`   | string | ✅        | `"wompi_card"` \| `"wompi_pse"` \| `"wompi_nequi"`     |

### 📤 Response exitosa (201 Created)

```json
{
  "success": true,
  "statusCode": 201,
  "message": "Pedido creado correctamente.",
  "data": {
    "orderId": 101,
    "userId": 12,
    "status": "pending",
    "total": 5000000,
    "paymentUrl": "https://checkout.wompi.co/p/?public-key=...",
    "createdAt": "2026-03-17",
    "items": [...]
  }
}
```

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Creación exitosa de pedido
- **Precondición:** Carrito `id: 7` tiene ≥ 3 unidades, total ≥ $60.000 COP, stock disponible.
- **Acción:** `POST /api/v1/orders` con datos válidos.
- **Resultado esperado:** HTTP `201`, `status: "pending"`, `paymentUrl` presente.

### ❌ Caso 2: Total del pedido menor al mínimo
- **Precondición:** Carrito con total < $60.000 COP.
- **Resultado esperado:** HTTP `422`, `error_code: MINIMUM_ORDER_AMOUNT`.

### ❌ Caso 3: Menos de 3 unidades en el carrito
- **Precondición:** Carrito con total de unidades < 3.
- **Resultado esperado:** HTTP `422`, `error_code: MINIMUM_QUANTITY`.

### ❌ Caso 4: Stock insuficiente al crear el pedido
- **Precondición:** Un producto del carrito no tiene stock suficiente.
- **Resultado esperado:** HTTP `422`, `error_code: INSUFFICIENT_STOCK`. Stock no se descuenta.

### ❌ Caso 5: Fallo en el pago — transacción revertida
- **Precondición:** Wompi retorna error al iniciar el pago.
- **Resultado esperado:** HTTP `502`, pedido en `status: "failed"`, stock restaurado.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional
- [ ] La transacción atómica funciona correctamente (revertir en caso de fallo).
- [ ] Se aplican `MinimumOrderAmountException` y `MinimumQuantityException`.
- [ ] El carrito se vacía automáticamente al crear el pedido.
- [ ] `paymentUrl` retornado en la respuesta.

### 🧪 Pruebas Completadas
- [ ] Pruebas unitarias sobre `OrderService.crearPedido()`.
- [ ] Prueba de reversión de transacción ante fallo de pago.

### 📄 Documentación Técnica
- [ ] Endpoint documentado en Swagger / OpenAPI.

### 🔐 Manejo de Errores
- [ ] `422` para monto mínimo, cantidad mínima, stock insuficiente.
- [ ] `502` para fallo de pasarela de pago.
- [ ] `401` sin token.