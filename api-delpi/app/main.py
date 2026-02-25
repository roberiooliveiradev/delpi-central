# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.config import settings  # Configurações do .env
from app.routes import product_routes   # Rotas de produtos
from app.routes import system_routes   # Rotas de produtos
from app.routes import data_routes  # Rota genérica
from app.middleware.auth_middleware import jwt_middleware
from fastapi.middleware import Middleware
from fastapi.openapi.utils import get_openapi


# Instância principal do app FastAPI
app = FastAPI(
    title="API DELPI",
    description="API RESTful para integração com o TOTVS Protheus — compatível com agentes GPT.",
    version="1.0.0",
    root_path="/apps/api-delpi",  # 🔥 ESSENCIAL
    contact={
        "name": "Equipe de Integração DELPI",
        "email": "suporte@delpi.com.br",
    },
    servers=[
        {
            "url": "/apps/api-delpi",
            "description": "Servidor via Gateway DELPI Central"
        }
    ],
    openapi_tags=[
        {"name": "Auth", "description": "Autenticação via JWT"}
    ],
    openapi_schema=None,
)

# Adicionar definição global de Bearer Token ao Swagger
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes, 
        servers=app.servers,
    )


    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # Exigir Bearer globalmente por padrão
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Adicionar middleware de autenticação
app.middleware("http")(jwt_middleware)

# Adiciona compressão GZIP a todas as respostas
app.add_middleware(GZipMiddleware, minimum_size=1000)  # bytes

# Configuração do CORS (para permitir chamadas do agente GPT e outros clientes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, substitua por domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurações automáticas do agente GPT
app.state.agent_config = {
    "auto_execute_api": settings.AUTO_EXECUTE_API,
    "confirm_before_request": settings.CONFIRM_BEFORE_REQUEST,
    "show_payload_before_execute": settings.SHOW_PAYLOAD_BEFORE_EXECUTE,
}


# Rota raiz — teste rápido da API
@app.get("/", tags=["Health Check"])
def root():
    return {"status": "online", "message": "API TOTVS Protheus em execução 🚀"}

# Inclui rotas adicionais (ex: prospecção de dados)
app.include_router(product_routes.router, prefix="/products", tags=["products"])
app.include_router(system_routes.router, prefix="/system", tags=["system"])
app.include_router(data_routes.router, prefix="/data", tags=["data"])
# Execução direta (modo desenvolvimento)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(settings.PORT), reload=True)
