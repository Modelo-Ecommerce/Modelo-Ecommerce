# [HU-010] Consultar pedido

## 📖 Historia de Usuario

**Como** cliente o administrador autenticado,
**Quiero** consultar el detalle de un pedido por su ID,
**Para** conocer el estado actual, los productos incluidos, la información de pago y la dirección de envío.

---

## 🔁 Flujo Esperado

- El usuario envía el `orderId` como parámetro en la URL a `GET /api/v1/orders/{id}`.
- El sistema valida el token JWT.
- El sistema verifica que el pedido exista.
- Si el usuario tiene rol `client`, solo puede ver sus propios pedidos (valida que `userId` del pedido coincida con el del token).
- Si el usuario tiene rol `admin`, puede consultar cualquier pedido.
- El sistema retorna los datos completos del pedido incluyendo ítems, estado del pago y dirección de envío.

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `GET /api/v1/orders/{id}`.
- [ ] Se requiere token JWT (rol `client` o `admin`).
- [ ] Cliente: solo puede ver sus propios pedidos. Admin: puede ver cualquiera.
- [ ] La respuesta incluye el subobjeto `payment` con `paymentId` y `status`.
- [ ] La respuesta incluye `shippingAddress` y `items[]` completos.

### 2. 📋 Estructura de la información

- [ ] La respuesta exitosa cumple con la siguiente estructura:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Pedido encontrado.",
  "data": {
    "orderId": 101,
    "userId": 12,
    "status": "processing",
    "total": 5000000,
    "payment": {
      "paymentId": 55,
      "status": "approved"
    },
    "shippingAddress": {
      "street": "Cra 15 #30-12",
      "city": "Bucaramanga",
      "department": "Santander",
      "postalCode": "680001"
    },
    "items": [
      {
        "productId": 45,
        "productName": "Laptop Lenovo IdeaPad 3",
        "quantity": 2,
        "unitPrice": 2500000,
        "subtotal": 5000000
      }
    ],
    "createdAt": "2026-03-17"
  }
}
```

- [ ] Si el pedido no existe:

```json
{
  "success": false,
  "statusCode": 404,
  "message": "Pedido no encontrado.",
  "error": {
    "error_code": "ORDER_NOT_FOUND",
    "details": "El pedido con id 101 no existe en el sistema.",
    "timestamp": "2026-03-17"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoint

- **Método HTTP:** `GET`
- **Ruta:** `/api/v1/orders/{id}`
- **Autenticación requerida:** 🔐 JWT Requerido (cliente o admin)

### 📥 Request Body

No aplica. El `orderId` se envía como parámetro en la URL.

### 📤 Response exitosa (200 OK)

Ver estructura en sección "Estructura de la información" arriba.

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Cliente consulta su propio pedido
- **Precondición:** Pedido `id: 101` pertenece al usuario `id: 12`, token válido.
- **Acción:** `GET /api/v1/orders/101`.
- **Resultado esperado:** HTTP `200`, datos completos del pedido.

### ✅ Caso 2: Admin consulta pedido de cualquier usuario
- **Precondición:** Token con rol `admin`.
- **Acción:** `GET /api/v1/orders/101`.
- **Resultado esperado:** HTTP `200`, datos completos del pedido.

### ❌ Caso 3: Cliente intenta ver pedido de otro usuario
- **Precondición:** Pedido `id: 101` pertenece al usuario `id: 99`, token del usuario `id: 12`.
- **Resultado esperado:** HTTP `403 Forbidden`, `error_code: FORBIDDEN`.

### ❌ Caso 4: Pedido no encontrado
- **Acción:** `GET /api/v1/orders/9999`.
- **Resultado esperado:** HTTP `404 Not Found`, `error_code: ORDER_NOT_FOUND`.

### ❌ Caso 5: Sin token de autenticación
- **Resultado esperado:** HTTP `401 Unauthorized`.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional
- [ ] El endpoint retorna datos completos del pedido con `200 OK`.
- [ ] Se restringe el acceso del cliente a sus propios pedidos.
- [ ] El admin puede consultar cualquier pedido.

### 🧪 Pruebas Completadas
- [ ] Pruebas unitarias sobre `OrderService` y `findById()`.
- [ ] Prueba de restricción de acceso cliente vs admin.

### 📄 Documentación Técnica
- [ ] Endpoint documentado en Swagger / OpenAPI.

### 🔐 Manejo de Errores
- [ ] `404` si el pedido no existe.
- [ ] `403` si el cliente intenta ver un pedido que no le pertenece.
- [ ] `401` sin token.