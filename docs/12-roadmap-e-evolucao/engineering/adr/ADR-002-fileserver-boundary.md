# ADR-002 — Boundary de FILESERVER e documentos técnicos

- **Status:** Accepted para MVP read-only
- **Data:** 2026-09-11

## Contexto

Engenharia já possui desenhos acessados a partir do FILESERVER por backend. Há também documentos em compartilhamentos corporativos, mas expor um Explorer web ou aceitar paths enviados pelo cliente criaria risco de traversal, vazamento de estrutura interna e autorização inconsistente.

## Decisão

O Portal oferece **bibliotecas lógicas allowlisted**, resolvidas exclusivamente no backend.

```text
client: library_id + document_id opaco
→ engineering-api/api owner
→ config server-side resolve raiz
→ normalize + containment
→ RBAC + allowlist + size/MIME
→ stream/preview/download
```

MVP é read-only.

Desenhos existentes devem preferir contratos já maduros da `api-delpi`; outras bibliotecas só entram quando sua allowlist for aprovada.

## Proibições

- browser acessar share SMB/CIFS;
- expor `X:\...`, hostname, credencial ou path absoluto;
- aceitar path arbitrário no request;
- edição/upload de documento técnico no MVP sem ADR próprio;
- transformar índice derivado em source of truth.

## Segurança

- containment após `resolve`;
- allowlist de extensão/MIME;
- limite de tamanho;
- authorization no download atual;
- logs sem path sensível;
- auditoria quando política exigir;
- share indisponível retorna erro explícito, não fallback inseguro.

## Decisões ainda abertas

- bibliotecas P0 e suas raízes;
- preview Office;
- permission específica de desenhos vs produtos/documentos;
- indexação persistente por performance.
