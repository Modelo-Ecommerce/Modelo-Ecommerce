# ─────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA — crea la app FastAPI y registra los routers
# ─────────────────────────────────────────────────────────────

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.api.usuarioApi import router as usuario_router
from app.api.authApi import router as auth_router
from app.api.productoApi import router as producto_router
from app.api.carritoApi import router as carrito_router
from app.api.pedidoApi import router as pedido_router
from app.api.pagoApi import router as pago_router

app = FastAPI(
    title="Modelo Ecommerce API",
    description="API REST para sistema de comercio electrónico",
    version="1.0.0",
)

app.include_router(usuario_router)
app.include_router(auth_router)
app.include_router(producto_router)
app.include_router(carrito_router)
app.include_router(pedido_router)
app.include_router(pago_router)

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