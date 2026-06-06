# ─────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA — crea la app FastAPI y registra los routers
# ─────────────────────────────────────────────────────────────

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from app.api.usuarioApi import router as usuario_router
from app.api.authApi import router as auth_router
from app.api.productoApi import router as producto_router
from app.api.carritoApi import router as carrito_router
from app.api.pedidoApi import router as pedido_router
from app.api.pagoApi import router as pago_router
from app.api.inventarioApi import router as inventario_router
from app.repositories.usuarioRepository import usuario_repository

app = FastAPI(
    title="Modelo Ecommerce API",
    description="API REST para sistema de comercio electrónico",
    version="1.0.0",
)

# ── Rutas públicas ────────────────────────────────────────────
RUTAS_PUBLICAS = {
    "/",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/users/",
    "/api/v1/users/register",
    "/api/v1/auth/login",
    "/api/v1/payments/webhook",
}


@app.middleware("http")
async def validar_usuario_token(request: Request, call_next):
    path = request.url.path
    if (path in RUTAS_PUBLICAS or
        path.startswith("/docs") or
        path.startswith("/openapi") or
        path.startswith("/redoc") or
        (request.method == "GET" and path.startswith("/api/v1/products"))):
        return await call_next(request)

    authorization = request.headers.get("authorization") or \
                    request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        return await call_next(request)

    token = authorization.replace("Bearer ", "").strip()
    try:
        user_id_str, role = token.split(":")
        user_id = int(user_id_str)
    except Exception:
        return await call_next(request)

    usuario = usuario_repository.obtener_por_id(user_id)
    if not usuario:
        return JSONResponse(
            status_code=401,
            content={
                "success":    False,
                "statusCode": 401,
                "message":    "El usuario del token no existe. Regístrate primero.",
                "error":      {"error_code": "USER_NOT_FOUND_IN_TOKEN"}
            }
        )
    return await call_next(request)


app.include_router(usuario_router)
app.include_router(auth_router)
app.include_router(producto_router)
app.include_router(carrito_router)
app.include_router(pedido_router)
app.include_router(pago_router)
app.include_router(inventario_router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "bearerAuth": {"type": "http", "scheme": "bearer"}
    }
    for path in schema["paths"].values():
        for method in path.values():
            method["security"] = [{"bearerAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi


@app.get("/", tags=["Root"])
def root():
    return {
        "mensaje": "API Ecommerce corriendo correctamente 🚀",
        "docs":    "http://127.0.0.1:8000/docs",
        "version": "1.0.0",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)