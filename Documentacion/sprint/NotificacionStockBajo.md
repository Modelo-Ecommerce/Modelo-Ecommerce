# [HU-018] Notificación de stock bajo

## 📖 Historia de Usuario

**Como** administrador del sistema,
**Quiero** recibir una notificación automática cuando el stock de un producto llegue a un nivel crítico (≤ 5 unidades),
**Para** tomar acciones oportunas de reabastecimiento y evitar la venta de productos sin disponibilidad.

---

## 🔁 Flujo Esperado

- El sistema detecta automáticamente que el stock de un producto quedó en un nivel igual o menor al umbral `LOW_STOCK_THRESHOLD=5` tras ejecutar una operación de `PATCH /api/v1/inventory/{productId}` o al confirmar un pedido vía `POST /api/v1/orders`.
- `InventoryService.notificarStockBajo()` es invocado internamente por `InventoryService.reducirStock()`.
- El sistema envía la notificación al **Servicio de Notificaciones** externo mediante `POST /api/v1/inventory/notify-low-stock`.
- El Servicio de Notificaciones recibe el payload y despacha la alerta al administrador (por correo u otro canal configurado).
- El sistema registra en la respuesta que la notificación fue enviada mediante el campo `lowStockNotified: true`.

> **Nota:** Esta historia corresponde a un proceso interno del sistema (`<include>` en el diagrama de casos de uso). No es invocada directamente por el administrador, sino activada automáticamente por `InventoryService` cuando se cumple la condición de stock bajo. El endpoint `POST /api/v1/inventory/notify-low-stock` es consumido internamente entre servicios.

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] `InventoryService.reducirStock()` verifica si `currentStock <= LOW_STOCK_THRESHOLD` tras cada actualización.
- [ ] Si la condición se cumple, se invoca automáticamente `InventoryService.notificarStockBajo()`.
- [ ] El sistema realiza una llamada interna a `POST /api/v1/inventory/notify-low-stock` con los datos del producto afectado.
- [ ] El umbral `LOW_STOCK_THRESHOLD=5` es configurable desde el archivo `.env` sin recompilar el sistema.
- [ ] La notificación se despacha al **Servicio de Notificaciones** externo.
- [ ] El campo `lowStockNotified` en la respuesta de `PATCH /api/v1/inventory/{productId}` indica si la notificación fue enviada.

### 2. 📆 Estructura de la información

- [ ] El payload enviado al Servicio de Notificaciones cumple con la siguiente estructura:

```json
{
  "event": "low_stock_alert",
  "data": {
    "productId": 45,
    "productName": "Laptop Lenovo IdeaPad 3",
    "currentStock": 4,
    "threshold": 5,
    "alertedAt": "2026-03-17T14:30:00Z"
  }
}
```

- [ ] La respuesta del endpoint `PATCH /api/v1/inventory/{productId}` incluye el campo `lowStockNotified` cuando aplica:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Stock actualizado correctamente. Se ha enviado alerta de stock bajo.",
  "data": {
    "productId": 45,
    "productName": "Laptop Lenovo IdeaPad 3",
    "previousStock": 7,
    "quantityChanged": 3,
    "currentStock": 4,
    "isLowStock": true,
    "lowStockNotified": true,
    "updatedAt": "2026-03-17"
  }
}
```

- [ ] Si el Servicio de Notificaciones falla, el sistema retorna igualmente `200 OK` en la actualización de stock, pero registra el fallo de notificación en los logs:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Stock actualizado correctamente. La notificación de stock bajo no pudo enviarse.",
  "data": {
    "productId": 45,
    "currentStock": 4,
    "isLowStock": true,
    "lowStockNotified": false,
    "updatedAt": "2026-03-17"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoint interno de notificación

- **Método HTTP:** `POST`
- **Ruta:** `/api/v1/inventory/notify-low-stock`
- **Autenticación requerida:** ✅ Sí (consumo interno entre servicios, token de servicio)
- **Invocado por:** `InventoryService.notificarStockBajo()` — **no es un endpoint público**

### 📥 Payload enviado al Servicio de Notificaciones

```json
{
  "event": "low_stock_alert",
  "data": {
    "productId": 45,
    "productName": "Laptop Lenovo IdeaPad 3",
    "currentStock": 4,
    "threshold": 5,
    "alertedAt": "2026-03-17T14:30:00Z"
  }
}
```

| Campo                  | Tipo   | Descripción                                        |
|------------------------|--------|----------------------------------------------------|
| `event`                | string | Identificador del tipo de evento: `low_stock_alert` |
| `data.productId`       | number | ID del producto con stock bajo                     |
| `data.productName`     | string | Nombre del producto                                |
| `data.currentStock`    | number | Stock actual después de la operación               |
| `data.threshold`       | number | Umbral configurado (`LOW_STOCK_THRESHOLD`)          |
| `data.alertedAt`       | string | Timestamp ISO 8601 del momento de la alerta        |

### ⚙️ Variable de entorno relevante

```env
LOW_STOCK_THRESHOLD=5
```
> Si la tienda necesita cambiar el umbral de alerta a 10 unidades, solo se actualiza esta variable en el `.env` sin modificar ni recompilar el código.

### 📤 Response del Servicio de Notificaciones (200 OK)

```json
{
  "success": true,
  "message": "Notificación de stock bajo enviada correctamente.",
  "notificationId": "notif_abc123"
}
```

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Notificación enviada automáticamente al reducir stock

- **Precondición:** El producto con `id: 45` tiene `currentStock: 7`. Se ejecuta `PATCH /api/v1/inventory/45` con `operation: "decrease"`, `quantity: 3`.
- **Resultado esperado:**
  - `currentStock: 4`, `isLowStock: true`
  - `notificarStockBajo()` es invocado
  - `lowStockNotified: true` en la respuesta
  - El Servicio de Notificaciones recibe el payload correctamente

### ✅ Caso 2: Stock exactamente en el umbral (5 unidades)

- **Precondición:** El producto tiene `currentStock: 8`. Se descuentan 3 unidades.
- **Resultado esperado:**
  - `currentStock: 5`, `isLowStock: true`
  - La notificación se activa (el umbral incluye el valor exacto)

### ✅ Caso 3: Stock por encima del umbral — sin notificación

- **Precondición:** El producto tiene `currentStock: 15`. Se descuentan 5 unidades.
- **Resultado esperado:**
  - `currentStock: 10`, `isLowStock: false`
  - `notificarStockBajo()` **no** es invocado
  - `lowStockNotified: false` o campo ausente en la respuesta

### ❌ Caso 4: Fallo del Servicio de Notificaciones

- **Precondición:** El Servicio de Notificaciones externo no está disponible (timeout o error 503).
- **Resultado esperado:**
  - La actualización de stock se completa exitosamente con `200 OK`
  - `lowStockNotified: false`
  - El error del servicio externo queda registrado en los logs del sistema
  - **No se lanza excepción al cliente** por fallo del servicio externo

### ✅ Caso 5: Notificación activada por confirmación de pedido

- **Precondición:** Al confirmar un pedido vía `POST /api/v1/orders`, `OrderService` llama a `InventoryService.reducirStock()` y el stock resultante queda ≤ 5.
- **Resultado esperado:**
  - La notificación se activa desde el flujo de pedido, no solo desde actualizaciones manuales
  - El campo `isLowStock: true` queda registrado en el inventario

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] `InventoryService.notificarStockBajo()` se invoca automáticamente cuando `currentStock <= LOW_STOCK_THRESHOLD`.
- [ ] El umbral es configurable desde `.env` sin modificar código.
- [ ] El sistema envía correctamente el payload al Servicio de Notificaciones externo.
- [ ] Si el Servicio de Notificaciones falla, la operación de inventario **no se revierte** y el fallo queda en logs.
- [ ] El campo `lowStockNotified` en la respuesta indica si la notificación fue enviada.

### 🧪 Pruebas Completadas

- [ ] Prueba unitaria de `InventoryService.notificarStockBajo()` con stock en umbral exacto.
- [ ] Prueba de integración: actualización de stock activa notificación al servicio externo.
- [ ] Prueba de resiliencia: fallo del Servicio de Notificaciones no interrumpe la operación de inventario.
- [ ] Prueba de activación desde flujo de pedidos (`OrderService` → `InventoryService`).

### 📄 Documentación Técnica

- [ ] Endpoint interno `/api/v1/inventory/notify-low-stock` documentado en Swagger como uso interno.
- [ ] Se documenta la variable de entorno `LOW_STOCK_THRESHOLD` y su impacto.
- [ ] Se describe el payload enviado al Servicio de Notificaciones y la respuesta esperada.

### 🔐 Manejo de Errores

- [ ] Fallo del Servicio de Notificaciones → log de error, `lowStockNotified: false`, operación de stock exitosa.
- [ ] Código `503` si hay error de conexión con el servicio externo (solo en logs, no expuesto al cliente).
