# [HU-006] Consultar catálogo de productos

## 📖 Historia de Usuario

**Como** visitante o usuario autenticado del sistema,
**Quiero** explorar el catálogo de productos disponibles con opciones de filtrado y paginación,
**Para** encontrar fácilmente los productos que deseo comprar.

---

## 🔁 Flujo Esperado

- El usuario accede al endpoint `GET /api/v1/products`.
- El sistema retorna los productos con estado `active`.
- Opcionalmente, el usuario envía query params para filtrar por categoría, precio o paginar resultados.
- Para ver el detalle de un producto específico, se usa `GET /api/v1/products/{id}`.
- El sistema incluye `stock` e `imageUrl` en la respuesta para que el cliente visualice disponibilidad.

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone `GET /api/v1/products` — endpoint público, sin autenticación.
- [ ] Se expone `GET /api/v1/products/{id}` — endpoint público, sin autenticación.
- [ ] Los productos con estado `discontinued` **no aparecen** en la lista pública (regla de dominio).
- [ ] La respuesta incluye paginación: `total`, `page`, `limit`, `totalPages`.
- [ ] Se soportan los query params: `?category=`, `?minPrice=`, `?maxPrice=`, `?page=`, `?limit=` (default: 10).
- [ ] Si `page` o `limit` no se envían, se usan valores por defecto (`page=1`, `limit=10`).

### 2. 📋 Estructura de la información

- [ ] Response exitosa de `GET /api/v1/products`:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Catálogo obtenido correctamente.",
  "data": {
    "products": [
      {
        "id": 45,
        "name": "Laptop Lenovo IdeaPad 3",
        "price": 2500000,
        "stock": 15,
        "categoryId": 3,
        "imageUrl": "https://cdn.ecommerce.com/productos/45.jpg"
      }
    ],
    "pagination": {
      "total": 50,
      "page": 1,
      "limit": 10,
      "totalPages": 5
    }
  }
}
```

- [ ] Response exitosa de `GET /api/v1/products/{id}`:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Producto obtenido correctamente.",
  "data": {
    "id": 45,
    "name": "Laptop Lenovo IdeaPad 3",
    "description": "Laptop 15.6 pulgadas, 8GB RAM, 256GB SSD",
    "price": 2500000,
    "stock": 15,
    "categoryId": 3,
    "imageUrl": "https://cdn.ecommerce.com/productos/45.jpg",
    "createdAt": "2026-03-17"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método | Ruta                    | Autenticación | Propósito                    |
|--------|-------------------------|---------------|------------------------------|
| `GET`  | `/api/v1/products`      | 🔓 Público    | Listar catálogo con filtros  |
| `GET`  | `/api/v1/products/{id}` | 🔓 Público    | Detalle de un producto       |

### 📥 Query Params opcionales — `GET /api/v1/products`

| Param       | Tipo   | Descripción                             | Default |
|-------------|--------|-----------------------------------------|---------|
| `category`  | number | Filtrar por `categoryId`                | —       |
| `minPrice`  | number | Precio mínimo en COP                    | —       |
| `maxPrice`  | number | Precio máximo en COP                    | —       |
| `page`      | number | Número de página                        | 1       |
| `limit`     | number | Cantidad de productos por página        | 10      |

> `GET /api/v1/products/{id}`: No requiere body ni query params — el `{id}` va en la URL.

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Listado paginado sin filtros
- **Acción:** `GET /api/v1/products`.
- **Resultado esperado:** HTTP `200 OK`, lista de productos `active` con paginación `page=1`, `limit=10`.

### ✅ Caso 2: Listado filtrado por categoría y rango de precio
- **Acción:** `GET /api/v1/products?category=3&minPrice=100000&maxPrice=3000000`.
- **Resultado esperado:** HTTP `200`, solo productos que coincidan con los filtros.

### ✅ Caso 3: Detalle de producto por ID
- **Acción:** `GET /api/v1/products/45`.
- **Resultado esperado:** HTTP `200`, datos completos del producto incluyendo `description`.

### ✅ Caso 4: Producto `discontinued` no aparece en listado público
- **Precondición:** Producto `id: 45` tiene `status: "discontinued"`.
- **Acción:** `GET /api/v1/products`.
- **Resultado esperado:** El producto `id: 45` **no** aparece en el array `products`.

### ❌ Caso 5: Producto no encontrado por ID
- **Acción:** `GET /api/v1/products/9999`.
- **Resultado esperado:** HTTP `404 Not Found`, `error_code: PRODUCT_NOT_FOUND`.

### ❌ Caso 6: Parámetros de paginación inválidos
- **Acción:** `GET /api/v1/products?page=-1&limit=abc`.
- **Resultado esperado:** HTTP `400 Bad Request`, `error_code: VALIDATION_ERROR`.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional
- [ ] Ambos endpoints retornan correctamente los datos.
- [ ] Productos `discontinued` excluidos del listado público.
- [ ] Paginación y filtros funcionan correctamente.

### 🧪 Pruebas Completadas
- [ ] Pruebas unitarias sobre `ProductService` y `findAll()`, `findById()`.
- [ ] Prueba de exclusión de productos descontinuados.

### 📄 Documentación Técnica
- [ ] Ambos endpoints documentados en Swagger / OpenAPI con query params detallados.

### 🔐 Manejo de Errores
- [ ] `404` si el producto no existe.
- [ ] `400` para parámetros de paginación inválidos.
- [ ] `503` si la base de datos no está disponible.