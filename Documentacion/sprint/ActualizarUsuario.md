# [HU-003] Gestión de perfil de usuario

## 📖 Historia de Usuario

**Como** usuario autenticado del sistema (cliente o administrador),
**Quiero** poder consultar, actualizar o eliminar mi perfil,
**Para** mantener mis datos personales actualizados y gestionar mi cuenta en la plataforma.

---

## 🔁 Flujo Esperado

**Actualizar perfil:**
- El usuario autenticado envía los campos a modificar a `PUT /api/v1/users/{id}`.
- El sistema valida el token JWT.
- El sistema verifica que el `userId` exista en la base de datos.
- Si se envía un nuevo `email`, se valida que no esté registrado por otro usuario.
- Si se envía un nuevo `phone`, se aplica la regla de dominio `InvalidColombianPhoneException`.
- El sistema persiste los cambios y retorna el perfil actualizado.

**Consultar perfil:**
- El usuario autenticado solicita sus datos con `GET /api/v1/users/{id}`.
- El sistema retorna la información del usuario (sin contraseña).

**Eliminar usuario:**
- El administrador envía `DELETE /api/v1/users/{id}`.
- El sistema valida que el usuario exista y procede a eliminarlo.

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone `PUT /api/v1/users/{id}` para actualizar perfil — requiere JWT (cualquier rol).
- [ ] Se expone `GET /api/v1/users/{id}` para consultar usuario — requiere JWT (cualquier rol).
- [ ] Se expone `DELETE /api/v1/users/{id}` para eliminar usuario — requiere JWT con rol `admin`.
- [ ] Si se actualiza `email`, se verifica que no esté duplicado en otro usuario.
- [ ] Si se actualiza `phone`, se aplica la regla de dominio `InvalidColombianPhoneException`.
- [ ] El cliente solo puede ver/editar su propio perfil; el admin puede acceder a cualquiera.

### 2. 📋 Estructura de la información

- [ ] Response exitosa de `PUT` y `GET`:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Usuario encontrado.",
  "data": {
    "id": 12,
    "name": "Albert Jaimes",
    "email": "albert@mail.com",
    "phone": "3001234567",
    "role": "client",
    "updatedAt": "2026-03-17"
  }
}
```

- [ ] Response exitosa de `DELETE` (204 No Content o 200):

```json
{
  "success": true,
  "statusCode": 204,
  "message": "Usuario eliminado correctamente.",
  "data": { "userId": 12, "deletedAt": "2026-03-17" }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

| Método   | Ruta                  | Autenticación       | Propósito              |
|----------|-----------------------|---------------------|------------------------|
| `PUT`    | `/api/v1/users/{id}`  | 🔐 JWT (cualquier rol) | Actualizar perfil   |
| `GET`    | `/api/v1/users/{id}`  | 🔐 JWT (cualquier rol) | Consultar usuario   |
| `DELETE` | `/api/v1/users/{id}`  | 🛡️ Solo Admin         | Eliminar usuario    |

### 📥 Request Body — `PUT /api/v1/users/{id}`

```json
{
  "name": "Albert Jaimes Actualizado",
  "email": "albert_nuevo@mail.com",
  "phone": "3109876543"
}
```

| Campo   | Tipo   | Requerido  | Validación                              |
|---------|--------|------------|-----------------------------------------|
| `name`  | string | ❌ Opcional | Mínimo 3 caracteres                    |
| `email` | string | ❌ Opcional | Formato válido, único en el sistema    |
| `phone` | string | ❌ Opcional | 10 dígitos, inicia en 3 (colombiano)  |

> `GET` y `DELETE`: No requieren body — el `{id}` va como parámetro en la URL.

### 📤 Response exitosa `PUT` / `GET` (200 OK)

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Perfil actualizado correctamente.",
  "data": {
    "id": 12,
    "name": "Albert Jaimes Actualizado",
    "email": "albert_nuevo@mail.com",
    "phone": "3109876543",
    "role": "client",
    "updatedAt": "2026-03-17"
  }
}
```

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Actualización exitosa de nombre y teléfono
- **Precondición:** Usuario `id: 12` existe, token JWT válido.
- **Acción:** `PUT /api/v1/users/12` con `name` y `phone` nuevos.
- **Resultado esperado:** HTTP `200 OK`, campos actualizados en `data`.

### ✅ Caso 2: Consulta exitosa de perfil
- **Acción:** `GET /api/v1/users/12`.
- **Resultado esperado:** HTTP `200 OK`, datos del usuario (sin contraseña).

### ✅ Caso 3: Eliminación exitosa (admin)
- **Precondición:** Token con rol `admin`.
- **Acción:** `DELETE /api/v1/users/12`.
- **Resultado esperado:** HTTP `204` o `200`, usuario eliminado.

### ❌ Caso 4: Email ya registrado por otro usuario
- **Acción:** `PUT /api/v1/users/12` con email duplicado.
- **Resultado esperado:** HTTP `409 Conflict`, `error_code: EMAIL_ALREADY_EXISTS`.

### ❌ Caso 5: Teléfono con formato inválido
- **Acción:** Enviar `phone: "123456789"`.
- **Resultado esperado:** HTTP `400 Bad Request`, `error_code: INVALID_PHONE_FORMAT`.

### ❌ Caso 6: Usuario no encontrado
- **Acción:** `PUT /api/v1/users/9999`.
- **Resultado esperado:** HTTP `404 Not Found`, `error_code: USER_NOT_FOUND`.

### ❌ Caso 7: DELETE sin rol admin
- **Precondición:** Token con rol `client`.
- **Acción:** `DELETE /api/v1/users/12`.
- **Resultado esperado:** HTTP `403 Forbidden`, `error_code: FORBIDDEN`.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional
- [ ] `PUT`, `GET` y `DELETE` sobre `/api/v1/users/{id}` funcionan correctamente.
- [ ] `DELETE` restringido a rol `admin`.
- [ ] Se aplica `InvalidColombianPhoneException` en actualización.

### 🧪 Pruebas Completadas
- [ ] Pruebas unitarias sobre `UserService.actualizarPerfil()`.
- [ ] Casos de email duplicado, teléfono inválido y usuario no encontrado cubiertos.

### 📄 Documentación Técnica
- [ ] Los tres endpoints documentados en Swagger / OpenAPI.

### 🔐 Manejo de Errores
- [ ] `404` si el usuario no existe.
- [ ] `409` si el email ya está en uso.
- [ ] `400` para teléfono inválido.
- [ ] `401` si el token es inválido o no se envía.
- [ ] `403` si un cliente intenta hacer DELETE.