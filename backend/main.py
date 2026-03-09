"""
main.py
=======
Punto de entrada de la API. Registra los routers y sirve el frontend estático.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from auth import purge_expired_sessions
from routers import search, favorites, auth, tracking

app = FastAPI(
    title="Buscador de Alquileres España",
    description="Plataforma unificada de búsqueda de alquileres en España",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(search.router)
app.include_router(favorites.router)
app.include_router(auth.router)
app.include_router(tracking.router)

# Servir frontend estático
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Buscador de Alquileres España — API activa"}


@app.get("/admin")
async def admin_panel():
    admin_path = os.path.join(FRONTEND_DIR, "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    return JSONResponse({"error": "Panel no encontrado"}, status_code=404)


@app.get("/api/health")
async def health_check():
    purge_expired_sessions()
    return {"status": "ok", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


