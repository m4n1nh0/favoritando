from prometheus_client import Gauge, Counter, Histogram, generate_latest, REGISTRY

# Métricas Prometheus customizadas para a aplicação.
# Usadas para observabilidade e monitoramento via endpoints /metrics.


# Contador de requisições HTTP realizadas na API.
REQUESTS_TOTAL = Counter(
    'http_requests_total', 'Total HTTP requests made to the API', ['method', 'endpoint', 'status_code']
)

# Histograma para medir a duração das requisições HTTP.
REQUEST_DURATION_SECONDS = Histogram(
    'http_request_duration_seconds', 'HTTP request latencies in seconds', ['method', 'endpoint']
)

# Contador de usuários registrados com sucesso no sistema.
USERS_REGISTERED_TOTAL = Counter(
    'users_registered_total', 'Total number of users registered'
)

# Contador de produtos adicionados como favoritos por clientes.
FAVORITES_ADDED_TOTAL = Counter(
    'favorites_added_total', 'Total number of favorites added'
)

# Medida atual de clientes considerados "ativos".
ACTIVE_CLIENTS = Gauge(
    'active_clients', 'Number of active clients'
)
