import time

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from starlette.middleware.sessions import SessionMiddleware

from app.api.routers import auth_router, clientes_router, favoritos_router, produtos_router
from app.core.config import settings
from app.core.logger import logger
from app.util.metrics import REQUESTS_TOTAL, REQUEST_DURATION_SECONDS, generate_latest

logger.info("Aplicativo iniciando. Inicializacao do banco de dados tratada por init.sql.")

app = FastAPI(
    title="aiqfome - API de Produtos Favoritos",
    description="API RESTful Favoritando - Desafio aiqfome.",
    version="1.0.0",
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL
)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY_SESSION)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Middleware que calcula o tempo de processamento de cada requisição HTTP.

    - Adiciona o cabeçalho `X-Process-Time` à resposta com o tempo da requisição.
    - Registra métricas Prometheus (`REQUESTS_TOTAL`, `REQUEST_DURATION_SECONDS`).
    - Loga o método, endpoint, status e duração no logger.

    - request: Objeto da requisição HTTP.
    - call_next: Função para passar a requisição para o próximo handler.

    - return: Resposta HTTP com cabeçalho adicional.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    endpoint = request.url.path
    method = request.method
    status_code = response.status_code

    if endpoint != "/metrics":
        REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(process_time)

    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Request: {method} {endpoint} - Status: {status_code} - Time: {process_time:.4f}s")
    return response


app.include_router(auth_router.router)
app.include_router(clientes_router.router)
app.include_router(favoritos_router.router)
app.include_router(produtos_router.router)


@app.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
async def metrics_endpoint():
    """
    Exportação de métricas Prometheus.

    Fornece dados de métricas formatados para scraping por servidores Prometheus.
    Excluído da documentação da API pública (Swagger/ReDoc).

    - return: Métricas no formato `text/plain` compatível com Prometheus.
    """
    return generate_latest().decode("utf-8")


@app.get("/", tags=["health check"])
async def root():
    """
    Health check da API.

    Usado para verificar se o serviço está ativo.
    Pode ser utilizado por ferramentas de monitoração ou balanceadores de carga.

    - return: Mensagem de boas-vindas.
    """
    logger.debug("Endpoint de verificação de integridade acessado.")
    return {"message": "Bem-vindo a API de Produtos Favoritos do aiqfome!"}


@app.on_event("startup")
async def startup_event():
    """
    Evento disparado quando a aplicação é encerrada.

    Ideal para liberar recursos, encerrar conexões com banco de dados ou fazer flush de logs.
    """
    logger.info("Aplicacaoo iniciada.")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento disparado quando a aplicação é encerrada.

    Ideal para liberar recursos, encerrar conexões com banco de dados ou flush de logs.
    """
    logger.info("Aplicacao finalizada.")
