# aiqfome - API de Produtos Favoritos (v1.0 - Arquitetura DDD/Clean)

Esta é a minha versão do desafio proposto para API RESTful do aiqfome, construída com Python FastAPI, que incorpora uma 
**arquitetura orientada a objetos (POO) inspirada em DDD/Clean Architecture** para máxima organização, manutenibilidade e escalabilidade.

O projeto gerencia **usuários** (com perfis Admin e Cliente), **clientes** (entidades de negócio) e seus **produtos 
favoritos**. A API utiliza **IDs auto incrementais inteiros** para chaves primárias, inclui **autenticação JWT** (com PyJWT e HTTPBearer), 
**controle de acesso baseado em perfil** e **login com Google (apenas para clientes)**, além de servir como proxy para 
consulta de produtos em uma API externa, salvando uma replica dos dados no banco aiqfome quando selecionado os favoritos
visando a performace da aplicação.

Para garantir um ambiente de desenvolvimento e produção robusto, a solução integra **Docker e Docker Compose** com uma 
**stack completa de observabilidade (Prometheus, Grafana, Loki, Promtail)**. A inicialização do banco de dados é automatizada via script SQL.
Esta função de observalidade é algo que ja tinha em finalização para outro projeto meu no github ainda para subir, 
para monitorar ações da IA que desenvolvi para uso academico, quis trazer para este projeto para poder acompanhar em container se os requisito de 
desempenho e escalabilidade estavão sendo atendidos.

## Índice

-   [Pré-requisitos](#pré-requisitos)
-   [Configuração do Ambiente](#configuração-do-ambiente)
-   [Registro no Google Cloud Console](#registro-no-google-cloud-console)
-   [Variáveis de Ambiente](#variables-de-ambiente)
-   [Executando a Aplicação com Docker Compose](#executando-a-aplicação-com-docker-compose)
-   [Acessando as Ferramentas de Observabilidade](#acessando-as-ferramentas-de-observabilidade)
-   [Fluxo de Uso e Perfis](#fluxo-de-uso-e-perfis)
-   [Endpoints da API](#endpoints-da-api)
-   [Considerações de Segurança](#consideraciones-de-segurança)
-   [Testes Automatizados](#testes-automatizados)
-   [Estrutura do Projeto](#estrutura-do-projeto)
-   [Limpeza do Ambiente Docker](#limpeza-do-ambiente-docker)

## Pré-requisitos

Antes de começar, certifique-se de ter os seguintes softwares instalados:

-   **Docker Desktop** (inclui Docker Engine e Docker Compose)
-   **git** (opcional, para clonar o repositório)

## Configuração do Ambiente

1.  **Atenção a estrutura de arquivos** conforme o layout do projeto detalhado em "[Estrutura do Projeto](#estrutura-do-projeto)".
    * O arquivo `docker-entrypoint-initdb/init.sql` com o esquema do banco de dados e dados iniciais 
    (incluindo o usuário admin). **Lembre-se de substituir o hash da senha no `init.sql` pelo hash real da sua senha 
    * admin, caso não mude a senha é "favorito@123".**

2.  **Crie o arquivo `.env`** na raiz do projeto, com base no `.env.example` (veja a seção [Variáveis de Ambiente](#variables-de-ambiente)).

## Registro no Google Cloud Console

Para habilitar o login com Google:

1.  Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2.  Crie um novo projeto (ou selecione um existente).
3.  Vá para "APIs & Services" > "Credentials".
4.  Clique em "Create Credentials" > "OAuth client ID".
5.  Selecione "Web application".
6.  Dê um nome ao seu cliente OAuth.
7.  Em "Authorized redirect URIs", adicione:
    -   `http://localhost:8000/auth/google/callback` (para desenvolvimento local com Docker Compose)
    -   Se for implantar, adicione também a URL de produção da sua API (ex: `https://sua-api.com/auth/google/callback`).
8.  Clique em "Create".
9.  Você receberá seu **Client ID** e **Client Secret**. Guarde-os, pois serão usados nas variáveis de ambiente.

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto (mesmo nível da pasta `app`, `Dockerfile` e `docker-compose.yml`) com base no 
`.env.example` ou na env abaixo, pronta para executar via docker, exceto para login via google que deve seguir os 
orientaçãoe em "[Registro no Google Cloud Console](#registro-no-google-cloud-console)":

```dotenv
# .env
# Configurações do Banco de Dados
DATABASE_URL="postgresql+psycopg2://postgres:postgres@db:5432/aiqfome_db"

# URL da Fake Store API
FAKE_STORE_API_BASE_URL="https://fakestoreapi.com"

# Configurações JWT
JWT_SECRET_KEY="SUA_CHAVE_SECRETA_MUITO_FORTE_PARA_JWT_PRODUCAO"
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Configurações da Documentação (opcional, remova para desabilitar ou mude o caminho)
# Para ambiente de produção ser possivel desabilitar o swagger
DOCS_URL="/docs"
REDOC_URL="/redoc"

# Configurações para Google OAuth (OBRIGATÓRIO PARA LOGIN GOOGLE)
GOOGLE_CLIENT_ID="SEU_CLIENT_ID_DO_GOOGLE"
GOOGLE_CLIENT_SECRET="SEU_CLIENT_SECRET_DO_GOOGLE"
GOOGLE_REDIRECT_URI="http://localhost:8000/auth/google/callback" # Se subirem o serviço em um servidor use o seu dominio, não irá funcionar com localhost
GOOGLE_METADATA_URI="https://accounts.google.com/.well-known/openid-configuration" #Endereço padrão, mas caso muse acho melhor em .env
SECRET_KEY_SESSION=104f12d72707df3dac68e456d1c38410eafdbd9e19f0f7ac61724d41d0cd1eb6 #Pode usar esta se quiser eu quem gerei

# Configurações de Logging
LOG_LEVEL="INFO" # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## Importante:

  * Substitua as credenciais do banco de dados e `JWT_SECRET_KEY`.
  * OBTENHA E SUBSTITUA `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` do Google Cloud Console.
  * Certifique-se de que `GOOGLE_REDIRECT_URI` no `.env` e no Google Cloud Console sejam exatamente os mesmos.
  * Pode seguir o que deixei no `.env.exemple`, lá também há algumas dicas.

## Executando a Aplicação com Docker Compose

Certifique-se de que o Docker Desktop esteja em execução.

Limpe volumes existentes (importante para recriar o DB com o SQL):

```bash
docker-compose down --volumes
```

Construa as imagens e inicie todos os serviços:

```bash
docker-compose up --build
```

  * `--build`: Garante que as imagens Docker sejam construídas (ou reconstruídas) antes de iniciar os contêineres.

Aguarde a inicialização: Os serviços de banco de dados, Prometheus, Grafana, Loki e Promtail podem levar alguns minutos 
para iniciar completamente. Você pode verificar o status:

```bash
docker-compose ps
```

E acompanhar os logs:

```bash
docker-compose logs -f
```

A API estará acessível em [http://localhost:800](http://localhost:8000), 
porém o swagger está acessível em [http://localhost:8000/docs](http://localhost:8000/docs).

O banco de dados será inicializado com as tabelas, o usuário admin e clientes (se incluído no `init.sql`) 
automaticamente na primeira vez que o serviço `db` for iniciado com um volume de dados vazio.

## Acessando as Ferramentas de Observabilidade

Após os serviços subirem:

  * **Prometheus UI**: [http://localhost:9090](https://www.google.com/search?q=http://localhost:9090)
    Aqui você pode ver o status da coleta de métricas e executar queries PromQL. Vá em "Status" -\> "Targets" para 
    verificar se a API está sendo scrapeada.
  * **Grafana Dashboard**: [http://localhost:3000](https://www.google.com/search?q=http://localhost:3000)
    Faça login com usuário `admin` e senha `admin`.
    Os data sources Prometheus e Loki já deverão estar provisionados.
    Para ver os logs, vá em "Explore" (ícone de bússola na barra lateral), selecione o data source Loki. Você pode usar 
    queries LogQL para filtrar logs (ex: `{container_name="aiqfome-api-1"}`). Os logs serão no formato JSON.
    Para métricas, selecione o data source Prometheus em "Explore" ou crie dashboards usando as métricas expostas pela 
    API (e.g., `http_requests_total`, `http_request_duration_seconds_bucket`).
    * Ou pode ir em dashboards e acompanhar algumas metricas em `aiqfome-api-overview`.
    * ATENCAO: ao logar no grafana que irá solicitar que refaça a senha, use a mesma desse help.

## Fluxo de Uso e Perfis

Esta API agora suporta dois perfis principais de usuário: **Admin** e **Cliente**.

  * **Registro de Usuários (Auto-serviço para Clientes)**:

      * Use `POST /auth/register` para que novos usuários (clientes) se cadastrem.
      * Esta rota é pública e sempre criará um usuário com o perfil `cliente`, associando-o automaticamente a uma nova 
        entidade Cliente na camada de negócio.

  * **Gerenciamento de Usuários por Administrador**:

      * Use `POST /auth/usuarios` (rota exclusiva para Admin) para que administradores possam criar novos usuários.
      * Um Admin pode especificar o perfil (`admin` ou `cliente`) para este novo usuário.
      * **Importante**: Usuraios criados por esta rota não terão uma entidade Cliente associada automaticamente.

  * **Login de Usuários**:

      * **Login Tradicional**: Use `POST /auth/login` com email(admin@aiqfome.com) e password(favorito@123) para obter um JWT (JSON Web Token).
        *   Usuario e senha fornecidos são para admin
        *   Para Cleintes já existem no init.sql alguns cadastrados, a senha é primeiro nome @123 ex: ana@123
      * **Login com Google (apenas para perfil cliente)**:
          * Inicie o fluxo acessando `GET http://localhost:8000/auth/google/login` no seu navegador. Isso redirecionará 
            para a página de consentimento do Google.
          * Após a autenticação no Google e consentimento, o Google o redirecionará de volta para
            `http://localhost:8000/auth/google/callback`. Este endpoint irá autenticar/registrar o usuário na sua API 
            (se for um novo cliente) e retornar um JWT da sua própria API.
      * Este JWT será usado no cabeçalho `Authorization: Bearer <token>` para acessar todas as rotas protegidas.

  * **Permissões**:

      * **Admin**: Pode gerenciar (criar, listar, atualizar, deletar) clientes (entidades de negócio) e usuários. Pode 
        ver e gerenciar favoritos de qualquer cliente.
      * **Cliente**: Pode visualizar seus próprios dados de usuário (`GET /auth/me`), e **gerenciar (adicionar, listar, deletar) 
        apenas os seus próprios produtos favoritos.**

## Endpoints da API

A API agora oferece os seguintes grupos de endpoints (acesse [http://localhost:8000/docs](https://www.google.com/search?q=http://localhost:8000/docs) para a documentação interativa):

### Autenticação (`/auth`)

  * `POST /auth/register`: **REGISTRO PÚBLICO** - Registra um novo usuário com e-mail/senha. (Perfil padrão: `cliente`, com criação de entidade Cliente associada).
  * `POST /auth/login`: Realiza o login tradicional e retorna um token JWT.
  * `POST /auth/usuarios`: **ADMIN CRIA USUÁRIO** - Permite a um administrador criar novos usuários (perfil 'admin' ou 'cliente').
      * Entrada obrigatória: `email`, `password`, `perfil`.
      * **Importante**: Usuários criados por esta rota **NÃO** terão uma entidade Cliente associada automaticamente.
  * `GET /auth/google/login`: Inicia o fluxo de login com Google.
  * `GET /auth/google/callback`: Endpoint de callback para o Google OAuth. Autentica/registra o usuário (cliente) e retorna o JWT da sua API.
  * `GET /auth/me`: Retorna os dados do usuário autenticado. (Protegida por JWT)

### Clientes (`/clientes`)

Todas as rotas de clientes são exclusivas para usuários com perfil `admin`.

  * `POST /clientes`: **ADMIN CRIA CLIENTE COM ACESSO** - Cria uma nova entidade Cliente **E** um usuário de login associado para ele. (Admin-only)
      * Entrada obrigatória: `nome`, `email`, `password`.
  * `GET /clientes`: Lista todos os clientes.
  * `GET /clientes/{cliente_id}`: Obtém detalhes de um cliente específico por ID.
  * `PUT /clientes/{cliente_id}`: Atualiza um cliente existente.
  * `DELETE /clientes/{cliente_id}`: Remova um cliente e todos os seus favoritos e o Usuario associado (se houver).

### Favoritos (`/clientes/{cliente_id}/favoritos`)

Estas rotas requerem autenticação JWT.

  * `POST /clientes/{cliente_id}/favoritos`: Adiciona um produto favorito.
      * **Clientes**: Podem adicionar favoritos apenas para seu próprio `cliente_id`.
      * **Administradores**: Podem adicionar favoritos para qualquer `cliente_id`.
      * Entrada: `produto_id` (ID do produto da Fake Store API). Os detalhes do produto são buscados e armazenados.
  * `GET /clientes/{cliente_id}/favoritos`: Lista produtos favoritos de um cliente.
      * **Clientes**: Podem listar apenas seus próprios favoritos.
      * **Administradores**: Podem listar favoritos de qualquer `cliente_id`.
  * `GET /clientes/{cliente_id}/favoritos/{favorito_id}`: Obtém um favorito específico.
      * **Clientes**: Podem ver apenas seus próprios favoritos.
      * **Administradores**: Podem ver favoritos de qualquer `cliente_id`.
  * `DELETE /clientes/{cliente_id}/favoritos/{favorito_id}`: Remove um produto favorito.
      * **Clientes**: Podem remover favoritos apenas da sua própria lista.
      * **Administradores**: Podem remover favoritos de qualquer `cliente_id`.

### Produtos (`/produtos`)

Estas rotas requerem autenticação JWT (qualquer perfil). Elas servem como um proxy para a [https://fakestoreapi.com](https://fakestoreapi.com).

  * `GET /produtos`: Lista todos os produtos disponíveis na Fake Store API.
  * `GET /produtos/{produto_id}`: Obtém os detalhes de um produto específico por ID da Fake Store API.

## Considerações de Segurança

  * **AVISO**: Para fins de desenvolvimento e demonstração, a segurança do Grafana foi configurada com credenciais 
    padrão (`admin`/`admin`). Logo para observalidade funcionar **faz necessario logar a primeira vez e colcoar mesma senha**.
  * **Loki e Promtail em Desenvolvimento**: Para simplicidade, as configurações do Loki e Promtail são básicas e 
    adequadas para um ambiente de desenvolvimento.
  * **Autenticação JWT (com PyJWT)**: O sistema usa tokens JWT para autenticar usuários, garantindo que apenas usuários 
    logados possam acessar recursos protegidos.
  * **Autorização Baseada em Perfil**: Dependências FastAPI garantem permissões corretas.
  * **Hash de Senhas**: As senhas são armazenadas como hashes bcrypt, nunca em texto puro.
  * **Validação de Dados**: O Pydantic é usado para validar os dados de entrada, prevenindo dados malformados.
  * **Tratamento de Exceções**: A API lida com erros de forma controlada, retornando mensagens claras e códigos de 
    status HTTP apropriados (`401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`).
  * **Google OAuth**: A autenticação é delegada ao Google, mas o sistema ainda emite um JWT próprio para gerenciar a 
    sessão interna, aumentando a segurança.

## Testes Automatizados

Este projeto possui testes automatizados desenvolvida com **pytest** e **FastAPI TestClient** para garantir a 
qualidade e o funcionamento correto das funcionalidades implementadas.

### O que foi testado

* Autenticação e autorização de usuários (login, registro e verificação do usuário atual).
* Operações CRUD dos clientes (criação, leitura, atualização e exclusão).
* Gerenciamento dos favoritos dos clientes (adicionar, listar, ler por ID e remover).
* Rotas protegidas com verificação de perfil e permissões.
* Cenários de sucesso e falha para garantir o tratamento adequado de erros e respostas HTTP.

### Como rodar os testes

1. Ative seu ambiente virtual (se estiver usando).
2. Execute o comando:

```bash
pytest -v
```

3. Para gerar relatório de cobertura, use:

```bash
pytest --cov=app --cov-report=html
```

O relatório HTML ficará disponível na pasta `htmlcov`, podendo ser aberto no navegador para análise detalhada.

### Resultados atuais

Os testes cobrem as principais funcionalidades da API e passam com sucesso, garantindo maior segurança para manutenção e evolução do sistema.

## Estrutura do Projeto

```
.
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── logger.py
│   ├── db/
│   │   ├── models/                 # Data Objects
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── cliente_model.py
│   │   │   ├── favorito_model.py
│   │   │   └── usuario_model.py
│   │   └── dto/                    # Data Transfer Objects
│   │   │   ├── __init__.py
│   │   │   ├── cliente_dto.py
│   │   │   ├── favorito_dto.py
│   │   │   └── usuario_dto.py
│   ├── api/
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth_router.py
│   │   │   ├── clientes_router.py
│   │   │   ├── favoritos_router.py
│   │   │   └── produtos_router.py
│   │   └── schemas/                # Schemas Pydantic
│   │   │   ├── __init__.py
│   │   │   ├── auth_schemas.py
│   │   │   ├── cliente_schemas.py
│   │   │   ├── favorito_schemas.py
│   │   │   └── usuario_schemas.py
│   ├── api/domain/                 # Lógica de negócio
│   │   ├── __init__.py
│   │   ├── cliente_domain.py
│   │   ├── favorito_domain.py
│   │   └── usuario_domain.py
│   ├── services/                   # Serviços Auxiliares / Integrações Externas
│   │   ├── __init__.py
│   │   ├── google_oauth_service.py
│   │   └── product_external_api.py
│   └── util/
│       ├── __init__.py
│       └── metrics.py
├── docker-entrypoint-initdb/       # Sobe junto ao docker, caso não queira 
│   └── init.sql                    # so criar o banco e carregar o script
├── .env.example
├── .dockerignore
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── prometheus.yml
├── promtail-config.yml
├── grafana/
│   └── provisioning/
│       └── dashboards/
│           ├── api_overview_dashboard.json
│           └── default.yaml
│       └── datasources/
│           └── datasource.yaml
├── docker-entrypoint-initdb/       # Serve para gerar passwaord e base para o init sql se precisar
│   ├── __init__.py
│   ├── generate-secret.py
│   └── generate_password.py
├── tests/       # Cobertura de teste das rotas, usando mock
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_clientes.py
│   ├── test_favoritos.py
│   └── test_produtos.py
└── README.md
```