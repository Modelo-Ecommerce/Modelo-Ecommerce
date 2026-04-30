# [HU-001] Iniciar sesión de usuario

## 📖 Historia de Usuario

**Como** usuario registrado del sistema (cliente o administrador),
**Quiero** autenticarme mediante mis credenciales (correo y contraseña),
**Para** acceder de forma segura a mi cuenta y a las funcionalidades protegidas del sistema.

---

## 🔁 Flujo Esperado

- El usuario envía su correo electrónico y contraseña al endpoint /api/v1/auth/login.
- El sistema valida que el correo exista en la base de datos.
- El sistema verifica que la contraseña coincida con el hash almacenado.
- El sistema verifica que el usuario no tenga estado `inactivo`.
- Si las credenciales son válidas, el sistema genera y retorna un token JWT.
- El cliente almacena el token para incluirlo en las siguientes solicitudes protegidas.

---

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST /api/v1/auth/login`.
- [ ] Se valida que el campo `email` tenga formato válido.
- [ ] Se valida que el campo `password` no esté vacío.
- [ ] Se verifica que el usuario exista en la tabla `users`.
- [ ] Se verifica que la contraseña coincida con el hash almacenado (bcrypt).
- [ ] Se verifica que el usuario no tenga estado `inactivo` (regla de dominio: `InactiveUserException`).
- [ ] Se genera un token JWT con `userId`, `email` y `role` en el payload.

### 2. 📆 Estructura de la información

- [ ] La respuesta exitosa cumple con la siguiente estructura:

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Inicio de sesión exitoso.",
  "data": {
    "userId": 12,
    "name": "Albert Jaimes",
    "email": "albert@mail.com",
    "role": "client",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

- [ ] Si las credenciales son incorrectas, el sistema retorna:

```json
{
  "success": false,
  "statusCode": 401,
  "message": "Credenciales inválidas.",
  "error": {
    "error_code": "INVALID_CREDENTIALS",
    "details": "El correo o la contraseña son incorrectos.",
    "timestamp": "2026-03-17"
  }
}
```

---

## 🔧 Notas Técnicas

### 🚀 Endpoint

- **Método HTTP:** `POST`
- **Ruta:** `/api/v1/auth/login`
- **Autenticación requerida:** ❌ No

### 📥 Request Body

```json
{
  "email": "albert@mail.com",
  "password": "Segura123!"
}
```

### 📤 Response exitosa (200 OK)

```json
{
  "success": true,
  "statusCode": 200,
  "message": "Inicio de sesión exitoso.",
  "data": {
    "userId": 12,
    "name": "Albert Jaimes",
    "email": "albert@mail.com",
    "role": "client",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

## 🧪 Requisitos de Pruebas

### ✅ Caso 1: Login exitoso con credenciales válidas

- **Precondición:** El usuario existe en la tabla `users` con estado `active`.
- **Acción:** Ejecutar `POST /api/v1/auth/login` con email y contraseña correctos.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Campo `token` presente en `data`
  - Campo `role` indica el rol del usuario (`client` o `admin`)

### ✅ Caso 2: Login con contraseña incorrecta

- **Precondición:** El usuario existe pero la contraseña enviada no coincide.
- **Acción:** Ejecutar `POST /api/v1/auth/login` con contraseña errónea.
- **Resultado esperado:**
  - Código HTTP `401 Unauthorized`
  - `error_code`: `INVALID_CREDENTIALS`

### ❌ Caso 3: Login con usuario inactivo

- **Precondición:** El usuario existe pero tiene estado `inactivo`.
- **Acción:** Ejecutar `POST /api/v1/auth/login` con credenciales correctas.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`
  - `error_code`: `INACTIVE_USER`
  - Mensaje: `"El usuario se encuentra inactivo y no puede iniciar sesión."`

### ❌ Caso 4: Login con email no registrado

- **Precondición:** El correo no existe en la base de datos.
- **Acción:** Ejecutar `POST /api/v1/auth/login`.
- **Resultado esperado:**
  - Código HTTP `401 Unauthorized`
  - `error_code`: `INVALID_CREDENTIALS`

### ❌ Caso 5: Campos vacíos o formato inválido

- **Precondición:** El body no contiene `email` o `password`, o el email tiene formato incorrecto.
- **Acción:** Ejecutar `POST /api/v1/auth/login` con datos inválidos.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - `error_code`: `VALIDATION_ERROR`

---

## ✅ Definición de Hecho

### 📦 Alcance Funcional

- [ ] El endpoint valida credenciales correctamente.
- [ ] El token JWT generado contiene `userId`, `email` y `role`.
- [ ] Se aplica la regla de dominio `InactiveUserException` para usuarios inactivos.

### 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias sobre `UserService.iniciarSesion()`.
- [ ] Se cubrieron todos los casos de error documentados.
- [ ] Las pruebas funcionales están documentadas y pasadas.

### 📄 Documentación Técnica

- [ ] Endpoint documentado en Swagger / OpenAPI.
- [ ] Se describe: propósito, campos de entrada y salida, respuesta exitosa y errores.

### 🔐 Manejo de Errores

- [ ] Código `401` para credenciales inválidas.
- [ ] Código `403` para usuario inactivo.
- [ ] Código `400` para validaciones de formato.
- [ ] Código `503` si la base de datos no está disponible.