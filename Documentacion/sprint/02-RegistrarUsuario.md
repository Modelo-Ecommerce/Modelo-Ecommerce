# [HU-002] Registrar usuario

## 📖 Historia de Usuario

**Como** visitante no autenticado del sistema,
**Quiero** crear una cuenta proporcionando mis datos personales,
**Para** poder acceder a la plataforma y realizar compras como cliente.

---

## 🔁 Flujo Esperado

- El visitante envía sus datos al endpoint `POST /api/v1/users o a `POST /api/v1/users/register` (alias del parcial — ambas apuntan al mismo controlador).
- El sistema valida que el `email` no esté ya registrado (`UserService` — validación de aplicación).
- El sistema valida que el `phone` sea colombiano: 10 dígitos, inicia en 3 (regla de dominio: `InvalidColombianPhoneException`).
- El sistema encripta la contraseña con bcrypt antes de almacenarla.
- El sistema crea el usuario con estado `active` y rol `client` por defecto.
- Si el registro falla por cualquier causa, no se persiste ningún dato (transacción atómica).
- El sistema retorna los datos del usuario creado (sin contraseña).

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone `POST /api/v1/users` como ruta REST principal.
- [ ] Se expone `POST /api/v1/users/register` como alias (equivalente, mismo controlador).
- [ ] Se valida que el `email` no esté duplicado en `users` (`UserService.registrarUsuario()`).
- [ ] Se valida que el `phone` sea colombiano: 10 dígitos, inicia en 3 (regla de dominio: `InvalidColombianPhoneException`).
- [ ] La contraseña se encripta con bcrypt antes de persistir.
- [ ] El usuario se crea con estado `active` por defecto.
- [ ] Si el registro falla, no se persiste ningún dato (transacción atómica).

### 2. 📋 Estructura de la información

- [ ] La respuesta exitosa cumple con la siguiente estructura:

```json
{
  "success": true,
  "statusCode": 201,
  "message": "Usuario registrado correctamente.",
  "data": {
    "id": 12,
    "name": "Albert Jaimes",
    "email": "albert@mail.com",
    "role": "client",
    "createdAt": "2026-03-17"
  }
}
```

- [ ] Si el correo ya está registrado, el sistema retorna:

```json
{
  "success": false,
  "statusCode": 409,
  "message": "El correo electrónico ya está registrado.",
  "error": {
    "error_code": "EMAIL_ALREADY_EXISTS",
    "details": "El correo albert@mail.com ya se encuentra asociado a una cuenta existente.",
    "timestamp": "2026-03-17"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoints

- **Método HTTP:** `POST`
- **Ruta principal (REST):** `/api/v1/users`
- **Alias (parcial del profesor):** `/api/v1/users/register`
- **Autenticación requerida:** 🔓 No (endpoint público)

> Ambas rutas apuntan al mismo controlador y retornan la misma respuesta. Se implementan las dos para cumplir tanto la convención REST como la referencia del parcial.

### 📥 Request Body

```json
{
  "name": "Albert Jaimes",
  "email": "albert@mail.com",
  "password": "Segura123!",
  "role": "client",
  "phone": "3001234567"
}
```

| Campo      | Tipo   | Requerido | Validación                             |
|------------|--------|-----------|----------------------------------------|
| `name`     | string | ✅        | Mínimo 3 caracteres                    |
| `email`    | string | ✅        | Formato válido, único en el sistema    |
| `password` | string | ✅        | Mínimo 8 caracteres                    |
| `role`     | string | ✅        | `"client"` o `"admin"`                 |
| `phone`    | string | ✅        | 10 dígitos, inicia en 3 (colombiano)  |

### 📤 Response exitosa (201 Created)

```json
{
  "success": true,
  "statusCode": 201,
  "message": "Usuario registrado correctamente.",
  "data": {
    "id": 12,
    "name": "Albert Jaimes",
    "email": "albert@mail.com",
    "role": "client",
    "createdAt": "2026-03-17"
  }
}
```

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Registro exitoso con datos válidos
- **Precondición:** El correo no existe en la base de datos.
- **Acción:** `POST /api/v1/users` con todos los campos válidos.
- **Resultado esperado:** HTTP `201 Created`, `data` contiene `id`, `name`, `email`, `role`, `createdAt`. La contraseña **no** aparece en la respuesta.

### ✅ Caso 2: Registro exitoso usando alias `/register`
- **Acción:** `POST /api/v1/users/register` con los mismos datos válidos.
- **Resultado esperado:** HTTP `201 Created`, misma respuesta que la ruta principal.

### ❌ Caso 3: Correo duplicado
- **Precondición:** `albert@mail.com` ya existe en la base de datos.
- **Resultado esperado:** HTTP `409 Conflict`, `error_code: EMAIL_ALREADY_EXISTS`.

### ❌ Caso 4: Teléfono con formato inválido
- **Acción:** Enviar `phone: "123456789"` (no inicia en 3 o menos de 10 dígitos).
- **Resultado esperado:** HTTP `400 Bad Request`, `error_code: INVALID_PHONE_FORMAT`.

### ❌ Caso 5: Contraseña con menos de 8 caracteres
- **Acción:** Enviar `password: "abc123"`.
- **Resultado esperado:** HTTP `400 Bad Request`, `error_code: VALIDATION_ERROR`.

### ❌ Caso 6: Campos obligatorios faltantes
- **Acción:** Enviar body sin `email` o `password`.
- **Resultado esperado:** HTTP `400 Bad Request`, `error_code: VALIDATION_ERROR`.

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional
- [ ] Ambas rutas (`/api/v1/users` y `/api/v1/users/register`) funcionan correctamente.
- [ ] La contraseña se almacena encriptada (nunca en texto plano).
- [ ] Se aplica `InvalidColombianPhoneException`.
- [ ] La transacción es atómica: si falla, no persiste ningún dato.

### 🧪 Pruebas Completadas
- [ ] Pruebas unitarias sobre `UserService.registrarUsuario()`.
- [ ] Prueba de regla de dominio del teléfono colombiano.
- [ ] Casos de duplicidad de correo y campos inválidos cubiertos.

### 📄 Documentación Técnica
- [ ] Ambos endpoints documentados en Swagger / OpenAPI.

### 🔐 Manejo de Errores
- [ ] `409` para correo duplicado.
- [ ] `400` para teléfono inválido, contraseña corta, campos vacíos.
- [ ] `503` si la base de datos no está disponible.