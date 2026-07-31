# CIPA API

API dedicada do plugin **CIPA** (Comissão Interna de Prevenção de Acidentes).

## Escopo v1

- Atas de reunião (CRUD, versionamento, participantes, signatários)
- Cadastro histórico de membros/cargos por filial (`cipa.manage`)
- Pesquisas SIPAT (wizard, link público, QR) — `cipa.sipat.view` / `cipa.sipat.manage`
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
- Membros CIPA: `GET/POST /members`, `PATCH /members/{id}`,
  `POST /members/{id}/end`, `DELETE /members/{id}` (soft-delete)
- SIPAT (auth): `GET/POST /sipat/surveys`, `GET/PATCH /sipat/surveys/{id}`,
  `POST …/clone`, `POST …/publish`, `POST …/close`, `GET …/qr`, `GET …/summary`,
  `GET …/export.xlsx`
- SIPAT (público): `GET /public/sipat/{token}`, `POST /public/sipat/{token}/responses`
  → formulário em `/p/cipa/sipat/{token}`

### SIPAT

Migration `V006__sipat_surveys.sql`. QR em `CIPA_SIPAT_QR_DIR` (volume
`cipa/sipat-qr`). Link: `{PUBLIC_BASE_URL}/p/cipa/sipat/{token}`. Respostas
anônimas (sem PII). `POST …/clone` cria rascunho com as mesmas perguntas
(título «Cópia de …»), sem token/QR/respostas — edição no wizard antes de publicar.

### Membros (`cipa.members`)

Tabela com mandato (`mandate_start` / `mandate_end`), cargo
(`president`, `vice_president`, `secretary`, `titular_member`, `alternate_member`)
e soft-delete. Regras: um usuário ativo por filial; um ocupante ativo por cargo
de liderança. `GET /members?unit_code=&active_on=` retorna a composição vigente
para pré-carga de novas atas.

## Stack

FastAPI · Postgres (`schema cipa`) · `delpi_auth` · bleach · ReportLab · qrcode[pil]

## Desenvolvimento

```bash
cd cipa-api
pip install -r requirements.txt
pip install -e ../shared[fastapi]
pytest -q
```

Migrations: `CIPA_RUN_MIGRATIONS_ON_STARTUP=true` no Compose.

Volumes persistentes: `cipa/signatures` (inclui `profiles/` para assinatura pessoal),
`cipa/attachments`, `cipa/pdfs`, `cipa/sipat-qr` sob `DELPI_DATA_HOST_DIR`.

O PDF final é gerado após todas as assinaturas e persistido em
`cipa/pdfs/{filial}/{ata}/final.pdf`. O código de validação é criado antes da
renderização, garantindo que o valor impresso seja o mesmo armazenado no banco.
