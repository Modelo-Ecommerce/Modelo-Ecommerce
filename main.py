# ─────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA — crea la app FastAPI y registra los routers
# ─────────────────────────────────────────────────────────────

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.api.usuarioApi import router as usuario_router
from app.api.authApi import router as auth_router

app = FastAPI(
    title="Modelo Ecommerce API",
    description="API REST para sistema de comercio electrónico",
    version="1.0.0",
)

# Registrar routers
app.include_router(usuario_router)
app.include_router(auth_router)

# ── Botón Authorize en Swagger ────────────────────────────────
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
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
        }
    }
    # Aplica seguridad a todos los endpoints
    for path in schema["paths"].values():
        for method in path.values():
            method["security"] = [{"bearerAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi

# Ruta raíz — bienvenida
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