# CIPA API

API dedicada do plugin **CIPA** (Comissão Interna de Prevenção de Acidentes).

## Escopo v1

- Atas de reunião (CRUD, versionamento, participantes, signatários)
- Assinatura manuscrita (PNG) vinculada ao hash da versão
- Perfil de assinatura pessoal por usuário (`cipa.sign`) — nome + PNG reutilizável
- Auditoria de domínio, PDF oficial formal e isolamento por filial `01`/`02`

## Rotas

- Health: `GET /health` → via gateway `/apps/cipa-api/health`
- Escopo RBAC: `GET /access` → unidades e capacidades do usuário
- Atas: `/minutes` (ver OpenAPI `/docs`)
- PDF oficial: `GET /minutes/{id}/export.pdf`
- Imagem de assinatura para leitura autenticada:
  `GET /minutes/{id}/signatures/{signature_id}/image`
- Assinatura pessoal: `GET/PUT /signatures/me`, `POST/GET /signatures/me/image`

## Stack

FastAPI · Postgres (`schema cipa`) · `delpi_auth` · bleach · ReportLab

## Desenvolvimento

```bash
cd cipa-api
pip install -r requirements.txt
pip install -e ../shared[fastapi]
pytest -q
```

Migrations: `CIPA_RUN_MIGRATIONS_ON_STARTUP=true` no Compose.

Volumes persistentes: `cipa/signatures` (inclui `profiles/` para assinatura pessoal), `cipa/attachments`, `cipa/pdfs` sob `DELPI_DATA_HOST_DIR`.

O PDF final é gerado após todas as assinaturas e persistido em
`cipa/pdfs/{filial}/{ata}/final.pdf`. O código de validação é criado antes da
renderização, garantindo que o valor impresso seja o mesmo armazenado no banco.
