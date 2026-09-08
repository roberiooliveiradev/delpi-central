# 📌 DELPI Central — Registro Oficial
## FASE 0 — Fundação Infra

Status: ✅ Concluída
Ambiente: Desenvolvimento Local (Windows + WSL2 + Docker)

---

# 🎯 Objetivo da Fase 0

Estabelecer a base estrutural mínima da plataforma DELPI Central com:

- Infraestrutura Docker funcional
- Gateway como ponto único de entrada
- Identity Provider (Keycloak)
- Banco de dados PostgreSQL (Core)
- Core API mínima funcional
- Portal React base
- Integração via rede Docker

Sem RBAC ainda.
Sem validação JWT ainda.
Sem plugins ainda.

Apenas fundação arquitetural.

---

# 🏗 Arquitetura Implementada

## Estrutura de Serviços

- gateway (Nginx)
- portal (React + Vite)
- core-api (Flask)
- postgres-core
- keycloak
- keycloak-db

Todos os serviços executando via Docker Compose.

---

# 🌐 Fluxo Atual de Requisições

Browser
   ↓
Gateway (Nginx)
   ↓
├── / → Portal (Vite)
├── /core-api/* → Core API (Flask)
└── /auth/* → Keycloak

---

# 🐳 Infraestrutura Docker

## Docker Compose configurado com:

- Rede interna automática
- Volumes nomeados para bancos
- Build local para:
  - core-api
  - portal
  - gateway

## Volumes persistentes:

- postgres_core_data
- keycloak_data

## Ambiente de Execução

- Windows 11
- WSL2 (Ubuntu)
- Docker Desktop com integração WSL ativa

Correções realizadas:
- Permissão de usuário no grupo docker
- Ajuste de Dockerfiles vazios
- Correção de problema de permissão do Vite
- Ajuste de ordem de dependências

---

# 🧱 Core API (Base)

Tecnologia: Python + Flask

Endpoint implementado:

GET /core-api/health

Resposta:
{
  "status": "ok"
}

Servidor exposto em:
http://localhost/core-api/health

Sem conexão com banco ainda.
Sem JWT ainda.

---

# ⚛ Portal

Tecnologia: React + Vite

Executando em modo dev dentro do container.

Exposto via Gateway em:
http://localhost

Ainda sem autenticação.
Ainda sem consumo da Core API.

---

# 🔐 Keycloak

Imagem oficial (modo dev)

Acessível via:
http://localhost/auth

Usuário admin criado automaticamente.

Ainda sem:
- Realm personalizado
- Client configurado
- PKCE configurado
- Audience configurado

---

# 🗄 Bancos de Dados

## postgres-core
Banco destinado à Core API.
Ainda sem tabelas.

## keycloak-db
Banco exclusivo do Keycloak.
Schema inicial criado automaticamente.

---

# 📁 Estrutura Final do Projeto

/delpi-central
  /core-api
    /app
    Dockerfile
    requirements.txt
  /portal
    /src
    Dockerfile
    package.json
  /gateway
    Dockerfile
    nginx.conf
  /infra
    docker-compose.yml
  README.md

---

# 🧠 Decisões Técnicas Consolidadas

✔ Uso de WSL2 para performance
✔ Docker como padrão obrigatório
✔ Gateway como entrada única
✔ Keycloak como Identity Provider oficial
✔ PostgreSQL separado para Core e IdP
✔ Containers independentes por serviço
✔ Estrutura pronta para RBAC
✔ Estrutura pronta para Plugin System

---

# 🚦 Critérios de Conclusão da Fase 0

- Todos containers sobem sem erro
- Core responde em /core-api/health
- Portal carrega via Gateway
- Keycloak acessível
- Bancos inicializados corretamente
- Rede Docker funcional

Todos critérios atendidos.

---

# 📌 Pronto para Fase 1

A base está estável e pronta para:

- Modelagem RBAC completa
- Integração JWT real
- Endpoint /core-api/me
- Sincronização automática de usuário
- Estrutura de auditoria
- Início do sistema de plugins

A Fase 0 estabeleceu a fundação estrutural da DELPI Central.

Sem atalhos.
Sem dívida técnica.
Infra sólida e validada.

---

Registro oficial encerrado.
FASE 0 concluída com sucesso. 🚀