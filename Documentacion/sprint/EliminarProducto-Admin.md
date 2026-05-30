# [HU-005] Eliminar y actualizar producto

## 📖 Historia de Usuario

**Como** administrador autenticado del sistema,
**Quiero** poder eliminar o actualizar los datos de un producto del catálogo,
**Para** mantener el catálogo vigente, corregir información errónea o retirar productos no disponibles.

---

## 🔁 Flujo Esperado

**Eliminar producto (`DELETE`):**
- El administrador envía el `productId` como parámetro en `DELETE /api/v1/products/{id}`.
- El sistema valida token JWT con rol `admin`.
- El sistema verifica que el producto exista.
- El sistema verifica que no existan pedidos activos (`pending` o `processing`) con ese producto.
- Si no hay pedidos activos, el producto se elimina (soft-delete: `status = "discontinued"`).

**Actualizar producto (`PUT`):**
- El administrador envía los campos a modificar a `PUT /api/v1/products/{id}`.
- El sistema valida token JWT con rol `admin`.
- El sistema verifica que el producto exista y que `categoryId` sea válido si se actualiza.
- El stock **no se actualiza aquí** — para eso existe el módulo de Inventario (`PATCH /api/v1/inventory/{productId}`).
- El sistema retorna los datos del producto actualizado.

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone `DELETE /api/v1/products/{id}` — requiere JWT con rol `admin`.
- [ ] Se expone `PUT /api/v1/products/{id}` — requiere JWT con rol `admin`.
- [ ] `DELETE`: verifica que no existan pedidos activos (`ProductService.eliminarProducto()`).
- [ ] `DELETE`: realiza soft-delete (`status = "discontinued"`), no borrado físico.
- [ ] `PUT`: el campo `stock` **no es actualizable** por este endpoint (usar módulo Inventario).
- [ ] `PUT`: si se envía `price`, se valida la regla de dominio `PriceBelowMinimumException`.

### 2. 📋 Estructura de la información

- [ ] Response exitosa de `DELETE`:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Producto eliminado correctamente.",
  "data": {
    "id": 45,
    "name": "Laptop Lenovo IdeaPad 3",
    "price": 2500000,
    "stock": 15,
    "status": "discontinued",
    "createdAt": "2026-03-17"
  }
}
```

- [ ] Response exitosa de `PUT`:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Producto actualizado correctamente.",
  "data": {
    "id": 45,
    "name": "Laptop Lenovo IdeaPad 3 Actualizado",
    "price": 2700000,
    "stock": 15,
    "status": "active",
    "createdAt": "2026-03-17"
  }
}
```

- [ ] Si el producto tiene pedidos activos (`DELETE`):

```json
{
  "success": false,
  "statusCode": 409,
  "message": "No se puede eliminar el producto porque tiene pedidos activos.",
  "error": {
    "error_code": "PRODUCT_HAS_ACTIVE_ORDERS",
    "details": "El producto con id 45 está asociado a pedidos en estado pending o processing.",
    "timestamp": "2026-03-17"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método   | Ruta                    | Autenticación  | Propósito               |
|----------|-------------------------|----------------|-------------------------|
| `DELETE` | `/api/v1/products/{id}` | 🛡️ Solo Admin   | Eliminar producto       |
| `PUT`    | `/api/v1/products/{id}` | 🛡️ Solo Admin   | Actualizar producto     |

### 📥 Request Body — `PUT /api/v1/products/{id}`

```json
{
  "name": "Laptop Lenovo IdeaPad 3 Actualizado",
  "description": "Laptop 15.6 pulgadas, 16GB RAM, 512GB SSD",
  "price": 2700000,
  "categoryId": 3
}
```

| Campo         | Tipo   | Requerido  | Validación                                   |
|---------------|--------|------------|----------------------------------------------|
| `name`        | string | ❌ Opcional | Mínimo 3 caracteres                          |
| `description` | string | ❌ Opcional | Texto descriptivo                            |
| `price`       | number | ❌ Opcional | Mínimo $10.000 COP (`PriceBelowMinimumException`) |
| `categoryId`  | number | ❌ Opcional | Debe existir en la base de datos             |

> `DELETE`: No requiere body — el `{id}` va como parámetro en la URL.
> El campo `stock` no es actualizable por `PUT`. Usar `PATCH /api/v1/inventory/{productId}`.

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Eliminación exitosa (soft-delete)
- **Precondición:** Producto `id: 45` existe, sin pedidos activos, token admin.
- **Acción:** `DELETE /api/v1/products/45`.
- **Resultado esperado:** HTTP `200`, `status: "discontinued"` en la respuesta.

### ✅ Caso 2: Actualización exitosa de nombre y precio
- **Precondición:** Producto existe, token admin válido.
- **Acción:** `PUT /api/v1/products/45` con `name` y `price` nuevos.
- **Resultado esperado:** HTTP `200 OK`, datos actualizados en `data`.

### ❌ Caso 3: DELETE con pedidos activos
- **Precondición:** Producto tiene pedidos en estado `pending` o `processing`.
- **Resultado esperado:** HTTP `409 Conflict`, `error_code: PRODUCT_HAS_ACTIVE_ORDERS`.

### ❌ Caso 4: PUT con precio por debajo del mínimo
- **Acción:** Enviar `price: 5000`.
- **Resultado esperado:** HTTP `422`, `error_code: PRICE_BELOW_MINIMUM`.

### ❌ Caso 5: Producto no encontrado
- **Acción:** `DELETE /api/v1/products/9999` o `PUT /api/v1/products/9999`.
- **Resultado esperado:** HTTP `404 Not Found`, `error_code: PRODUCT_NOT_FOUND`.

### ❌ Caso 6: Token con rol `client`
- **Resultado esperado:** HTTP `403 Forbidden`, `error_code: FORBIDDEN`.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional
- [ ] `DELETE` realiza soft-delete y valida pedidos activos.
- [ ] `PUT` actualiza campos permitidos (no `stock`).
- [ ] Solo rol `admin` puede acceder a ambos endpoints.

### 🧪 Pruebas Completadas
- [ ] Pruebas unitarias sobre `ProductService.eliminarProducto()` y `ProductService.actualizarProducto()`.
- [ ] Caso de producto con pedidos activos cubierto.

### 📄 Documentación Técnica
- [ ] Ambos endpoints documentados en Swagger / OpenAPI.

### 🔐 Manejo de Errores
- [ ] `409` para producto con pedidos activos.
- [ ] `404` para producto no encontrado.
- [ ] `422` para precio por debajo del mínimo.
- [ ] `403` para rol no autorizado.