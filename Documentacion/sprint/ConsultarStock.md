# [HU-016] Consultar stock de producto

## 📖 Historia de Usuario

**Como** administrador autenticado del sistema,
**Quiero** consultar el stock actual de un producto en el inventario,
**Para** conocer la disponibilidad de unidades y tomar decisiones de reabastecimiento.

---

## 🔁 Flujo Esperado

- El administrador envía el `productId` como parámetro en la URL a `GET /api/v1/inventory/{productId}`.
- El sistema valida el token JWT con rol `admin` (o `client` que tenga el producto en su carrito — ver nota).
- El sistema verifica que el `productId` exista en la tabla `products`.
- El sistema consulta la tabla `inventory` usando `IInventoryRepository.findByProductId()`.
- Si el stock es ≤ `LOW_STOCK_THRESHOLD` (5), el campo `isLowStock` retorna `true`.
- El sistema retorna el stock actual del producto.

> **Nota:** Este endpoint también es consumido **internamente** por `CartService` y `OrderService` para verificar disponibilidad antes de agregar productos al carrito o crear pedidos.

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `GET /api/v1/inventory/{productId}`.
- [ ] Se requiere token JWT (rol `admin` para uso directo; también consumido internamente).
- [ ] Se verifica que el `productId` exista en la tabla `products`.
- [ ] Se consulta `IInventoryRepository.findByProductId()`.
- [ ] El campo `isLowStock` es `true` si `currentStock <= LOW_STOCK_THRESHOLD` (configurable en `.env`, valor por defecto: 5).
- [ ] El campo retorna `stock` (nombre usado en la tabla del docx) y `lastUpdated`.

### 2. 📋 Estructura de la información

- [ ] La respuesta exitosa cumple con la siguiente estructura:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Stock consultado correctamente.",
  "data": {
    "productId": 45,
    "productName": "Laptop Lenovo IdeaPad 3",
    "stock": 13,
    "isLowStock": false,
    "lastUpdated": "2026-03-17"
  }
}
```

- [ ] Si el `productId` no existe:

```json
{
  "success": false,
  "statusCode": 404,
  "message": "Producto no encontrado.",
  "error": {
    "error_code": "PRODUCT_NOT_FOUND",
    "details": "El producto con id 45 no existe en el sistema.",
    "timestamp": "2026-03-17"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoint

- **Método HTTP:** `GET`
- **Ruta:** `/api/v1/inventory/{productId}`
- **Autenticación requerida:** 🔐 JWT Requerido (admin para uso directo; consumo interno por otros servicios)

### 📥 Request Body

No aplica. El `productId` se envía como parámetro en la URL.

### 📤 Response exitosa (200 OK)

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Stock consultado correctamente.",
  "data": {
    "productId": 45,
    "productName": "Laptop Lenovo IdeaPad 3",
    "stock": 13,
    "isLowStock": false,
    "lastUpdated": "2026-03-17"
  }
}
```

### ⚙️ Variable de entorno relevante

```env
LOW_STOCK_THRESHOLD=5
```

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Consulta exitosa con stock normal
- **Precondición:** Producto `id: 45` existe con `stock: 13`.
- **Acción:** `GET /api/v1/inventory/45`.
- **Resultado esperado:** HTTP `200`, `isLowStock: false`, `stock: 13`.

### ✅ Caso 2: Stock en nivel bajo (≤ 5 unidades)
- **Precondición:** Producto `id: 45` con `stock: 3`.
- **Acción:** `GET /api/v1/inventory/45`.
- **Resultado esperado:** HTTP `200`, `isLowStock: true`, `stock: 3`.

### ✅ Caso 3: Stock exactamente en el umbral (5 unidades)
- **Precondición:** Producto con `stock: 5`.
- **Resultado esperado:** HTTP `200`, `isLowStock: true`.

### ❌ Caso 4: Producto no encontrado
- **Acción:** `GET /api/v1/inventory/9999`.
- **Resultado esperado:** HTTP `404`, `error_code: PRODUCT_NOT_FOUND`.

### ❌ Caso 5: Sin token de autenticación
- **Resultado esperado:** HTTP `401 Unauthorized`.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional
- [ ] El endpoint retorna el stock actual del producto con `200 OK`.
- [ ] `isLowStock` refleja correctamente el umbral `LOW_STOCK_THRESHOLD=5` del `.env`.
- [ ] El endpoint es consumido correctamente por `CartService` y `OrderService` de forma interna.

### 🧪 Pruebas Completadas
- [ ] Pruebas unitarias sobre `InventoryService` consultando `findByProductId()`.
- [ ] Prueba de cálculo de `isLowStock` con stock en límite exacto (5 unidades).
- [ ] Prueba de producto inexistente.

### 📄 Documentación Técnica
- [ ] Endpoint documentado en Swagger / OpenAPI.

### 🔐 Manejo de Errores
- [ ] `404` si el producto no existe.
- [ ] `401` sin token.
- [ ] `503` si la base de datos no está disponible.