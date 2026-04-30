# [HU-004] Crear producto

## 📖 Historia de Usuario

**Como** administrador autenticado del sistema,
**Quiero** registrar nuevos productos en el catálogo con su nombre, descripción, precio y stock inicial,
**Para** que los clientes puedan visualizarlos y agregarlos a su carrito de compras.

---

## 🔁 Flujo Esperado

- El administrador envía los datos del producto al endpoint `POST /api/v1/products`.
- El sistema valida el token JWT y verifica que el rol sea `admin`.
- El sistema valida que el `categoryId` exista en la base de datos.
- El sistema valida que el precio sea mayor o igual a $10.000 COP (regla de dominio: `PriceBelowMinimumException`, umbral: `MIN_PRODUCT_PRICE=10000`).
- El sistema crea el producto con estado `active`.
- El sistema llama a `InventoryService` para inicializar el stock del nuevo producto automáticamente.
- El sistema retorna los datos del producto creado.

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST /api/v1/products`.
- [ ] Se requiere token JWT con rol `admin`.
- [ ] Se valida que `categoryId` exista en la base de datos.
- [ ] Se aplica la regla de dominio: precio mínimo `MIN_PRODUCT_PRICE` ($10.000 COP) — lanza `PriceBelowMinimumException`.
- [ ] Al crear el producto, `ProductService` llama automáticamente a `InventoryService` para inicializar el stock.
- [ ] El producto se crea con estado `active` y campo `status` en la respuesta.

### 2. 📋 Estructura de la información

- [ ] La respuesta exitosa cumple con la siguiente estructura:

```json
{
  "success": true,
  "statusCode": 201,
  "message": "Producto creado correctamente.",
  "data": {
    "id": 45,
    "name": "Laptop Lenovo IdeaPad 3",
    "price": 2500000,
    "stock": 15,
    "categoryId": 3,
    "status": "active",
    "createdAt": "2026-03-17"
  }
}
```

- [ ] Si el precio es menor al mínimo:

```json
{
  "success": false,
  "statusCode": 422,
  "message": "El precio del producto no cumple el mínimo requerido.",
  "error": {
    "error_code": "PRICE_BELOW_MINIMUM",
    "details": "El precio mínimo permitido es $10.000 COP (MIN_PRODUCT_PRICE).",
    "timestamp": "2026-03-17"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoint

- **Método HTTP:** `POST`
- **Ruta:** `/api/v1/products`
- **Autenticación requerida:** 🛡️ Solo Admin (JWT con rol `admin`)

### 📥 Request Body

```json
{
  "name": "Laptop Lenovo IdeaPad 3",
  "description": "Laptop 15.6 pulgadas, 8GB RAM, 256GB SSD",
  "price": 2500000,
  "stock": 15,
  "categoryId": 3
}
```

| Campo         | Tipo   | Requerido | Validación                                      |
|---------------|--------|-----------|-------------------------------------------------|
| `name`        | string | ✅        | Mínimo 3 caracteres                             |
| `description` | string | ✅        | Texto descriptivo del producto                  |
| `price`       | number | ✅        | Mínimo $10.000 COP (`MIN_PRODUCT_PRICE`)        |
| `stock`       | number | ✅        | Mayor o igual a 0                               |
| `categoryId`  | number | ✅        | Debe existir en la base de datos                |

### 📤 Response exitosa (201 Created)

```json
{
  "success": true,
  "statusCode": 201,
  "message": "Producto creado correctamente.",
  "data": {
    "id": 45,
    "name": "Laptop Lenovo IdeaPad 3",
    "price": 2500000,
    "stock": 15,
    "categoryId": 3,
    "status": "active",
    "createdAt": "2026-03-17"
  }
}
```

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Creación exitosa de producto
- **Precondición:** Token admin válido, `categoryId: 3` existe.
- **Acción:** `POST /api/v1/products` con datos válidos.
- **Resultado esperado:** HTTP `201 Created`, stock inicializado en `InventoryService`.

### ❌ Caso 2: Precio por debajo del mínimo
- **Acción:** Enviar `price: 5000`.
- **Resultado esperado:** HTTP `422 Unprocessable Entity`, `error_code: PRICE_BELOW_MINIMUM`.

### ❌ Caso 3: `categoryId` inexistente
- **Acción:** `POST /api/v1/products` con `categoryId: 999`.
- **Resultado esperado:** HTTP `404 Not Found`, `error_code: CATEGORY_NOT_FOUND`.

### ❌ Caso 4: Token con rol `client`
- **Resultado esperado:** HTTP `403 Forbidden`, `error_code: FORBIDDEN`.

### ❌ Caso 5: Campos obligatorios faltantes
- **Resultado esperado:** HTTP `400 Bad Request`, `error_code: VALIDATION_ERROR`.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional
- [ ] Endpoint crea el producto y retorna `201`.
- [ ] Se aplica `PriceBelowMinimumException` (mínimo `MIN_PRODUCT_PRICE`).
- [ ] Stock se inicializa automáticamente vía `InventoryService`.
- [ ] Solo usuarios con rol `admin` pueden acceder.

### 🧪 Pruebas Completadas
- [ ] Pruebas unitarias sobre `ProductService.crearProducto()`.
- [ ] Prueba de regla de dominio: precio mínimo.
- [ ] Prueba de validación de `categoryId`.

### 📄 Documentación Técnica
- [ ] Endpoint documentado en Swagger / OpenAPI.

### 🔐 Manejo de Errores
- [ ] `422` para precio por debajo del mínimo.
- [ ] `404` para categoría inexistente.
- [ ] `403` para rol no autorizado.
- [ ] `400` para campos faltantes o inválidos.