from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# CORS enabled to allow requests from the Flutter mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.endpoints import generation, audit, admin, auth, admin_rag, id_generation, multimodal, chat

app.include_router(generation.router, prefix="/api/v1/generation", tags=["Draft Generation"])
app.include_router(audit.router, prefix="/api/v1/documents", tags=["Audit & Compliance"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin Management"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(admin_rag.router, prefix="/api/v1/admin", tags=["RAG Management"])
app.include_router(id_generation.router, prefix="/api/v1/id-processing", tags=["ID Processing"])
app.include_router(multimodal.router, prefix="/api/v1/multimodal", tags=["Multimodal Features"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat History"])

@app.get("/")
def root():
    return {"message": f"Server for {settings.PROJECT_NAME} is up and running!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
