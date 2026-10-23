# X4.UX-R1.S7 — Federated Deploy & Runtime Acceptance (2026-10-23)

> Deploy dos 3 componentes do cadastro assistido por CNPJ + verificação de runtime
> em produção. Escrita ERP permanece OFF; smoke 100% read-only.

## 1. Baseline e decisão de deploy

| Item | Valor |
|---|---|
| Local HEAD (pós-rebase) | `54ad4cfb9e` = `origin/main` |
| SHAs S1/S2/R1/R2 ∈ HEAD | `1cdfa4a85a`, `b7f4a51ce6`, `cda28e6b9f`, `ddc5abb81d` — todos |
| Prod host | `srv-api` (`operador@192.168.1.237`), SSH chave OK |
| Prod checkout **antes** | `c0b61d3653` — **sem** S1/S2/R1/R2 → deploy necessário |
| Prod checkout **depois** | `54ad4cfb9e` (`git pull --ff-only`, limpo) |
| Migrations no range | **zero** (138 arquivos, nenhum `.sql`/migration) |
| Gate ERP prod | `PROTHEUS_SUPPLIER_CREATE_ENABLED=false`, `PROTHEUS_SUPPLIER_UPDATE_ENABLED=false` |

**Rollback targets:** SHA `c0b61d3653` + imagens anteriores
`infra-api-delpi:4bd0aab4e8de`, `infra-supplies-api:de4d4af5e989`,
`infra-supplies:7679f33853a3` (procedimento: `up-prod-sequential.sh --build <svc>`).

## 2. Deploy executado (ordem api-delpi → BFF → MFE)

| Serviço | Imagem antes → depois | Container |
|---|---|---|
| `delpi-api-delpi` | `4bd0aab4e8de` → **`12cda95ea1d2`** | Up, healthy, servindo tráfego real |
| `delpi-supplies-api` | `de4d4af5e989` → **`84d02964a88f`** | Up, healthy |
| `delpi-supplies` (MFE) | `7679f33853a3` → **`6b3130be529f`** | Up, nginx servindo |
| `external-data-api` | — | **SKIP** (sem mudança; healthy) |
| demais 90+ containers | — | preservados, uptime inalterado |

## 3. Runtime gates

### api-delpi
- `GET /supplies/suppliers?tax_id=…` registrado: sem credencial → **401** (não 404).
- Regressão `query` textual via BFF: `200`, 15 itens — LIKE intacto.
- Match exato comprovado end-to-end (ver POSSIBLE_MATCH abaixo).

### supplies-api `POST /suppliers/creation-preview`

| Cenário | Resultado |
|---|---|
| Sem token (público e interno) | **401** |
| CNPJ válido sem fornecedor (`00…0191`) | **200** `CLEAR` + **8 sugestões** BrasilAPI real, proveniência `brasilapi-cnpj-v1` + `retrieved_at` |
| CNPJ de fornecedor existente `002469/01` | **200** `POSSIBLE_MATCH`, match `002469/01` (nome + código + loja) |
| Dígito verificador inválido | **422 `invalid_request`** |
| Campo server-owned (`actor`) | **422 `unexpected fields`** |
| Campos LGPD (contact.*, email, phone…) | ausentes das sugestões; listados em `unavailable_fields` |
| `supplier_short_name` | retornado com `applicable:false` |
| `write_enabled` | `false` |
| Via gateway `/apps/supplies-api/…` | **200 CLEAR** (rota pública confirmada) |
| 403 (usuário sem permissão) | `TEST_NOT_RUN` — conta de smoke possui acesso; coberto por testes unitários |
| 429/Retry-After | `TEST_NOT_RUN` — proibido gerar rate-limit artificial em produção |
| `INCONCLUSIVE` (falha interna) | `TEST_NOT_RUN` — não se induz falha em produção |

### MFE federado
- `remoteEntry.js` público: `200 application/javascript`; expõe `__federation_expose_App-GsbycATr.js`.
- Bundle **`App-5YYpsuZ3.js`** (263 518 B — confere com build local): contém
  `creation-preview`, «Consultar por CNPJ», «Buscar por razão social»,
  «Usar CNPJ consultado no formulário» (R1), `identityBlocked` (R2),
  «Preencher manualmente», «em homologação».
- Bundle **limpo**: zero `api-delpi`, zero `brasilapi.com.br`, zero
  `Service-Authorization`/`s2s_`/`client_secret` → MFE é BFF-only.

### Não-escrita
- Logs `delpi-supplies-api` e `delpi-api-delpi` durante o smoke: **0** POST/PUT
  de fornecedores, 0 chamadas de escrita Protheus.
- Preview não persiste fornecedor nem revisão (read-only por contrato).

### Regressão
- E13 `GET /suppliers` → 200; `?query=` textual → 200.
- E14 `GET /suppliers/002469/01` → 200 (`sections`, `tax_id_masked`).

## 4. Visual / interativo

Sem ferramenta de navegador autenticado nesta execução → V1–V8
(desktop/mobile/temas/teclado/F5/modal) **`INCONCLUSIVE` / `TEST_NOT_RUN`**.
Acessibilidade estrutural já revisada em S2 (radiogroup, `aria-invalid`,
`role="alert"`, foco visível) — sem evidência de render real.

## 5. Resultado por gate

| Gate | Status |
|---|---|
| Inventário + pré-voo | PASS |
| Segurança pré-deploy | PASS (SHA/imagens/rollback/gate ERP OFF/nenhuma migration) |
| Deploy sequencial | PASS (3/3 componentes) |
| Runtime api-delpi | PASS (rota exata ativa, regressão LIKE) |
| Runtime supplies-api | PASS (401/422/200 CLEAR/POSSIBLE_MATCH via gateway) |
| Bundle federado | PASS (artefato real contém S2+R1+R2, BFF-only) |
| Não-escrita | PASS (logs limpos, `write_enabled:false`) |
| Visual/interativo | INCONCLUSIVE (sem browser) |
| Pós-condição | PASS (todos saudáveis, serviços alheios intactos) |

**AC:** 01–14, 17, 18 `PASS` · AC-15/16 `INCONCLUSIVE` (evidência visual pendente).

**Conclusão: `ACCEPT_WITH_RESIDUAL`** — integração completa comprovada em
produção via API e artefato federado; residual = validação visual interativa.


## 6. Revisão GPT / Architecture Acceptance — 2026-10-23

**Decisão de revisão: `ACCEPT_WITH_RESIDUAL` para o DEPLOY e os runtime checks executados.** A documentação S7 e o relatório do Cursor registram publicação dos três componentes, health e smoke real read-only (`CLEAR`, `POSSIBLE_MATCH`, 401/422, gateway BFF, bundle S2/R1/R2, E13/E14). Esta revisão conferiu a evidência registrada no GitHub; **não executou independentemente SSH, browser, nem testes de produção**. A ausência de POST/PUT nos logs foi observada durante a janela do smoke, não é prova abrangente de zero escritas em qualquer período.

**GATE-FEATURE integral = `INCONCLUSIVE`**, pois AC-15 e AC-16 e os cenários V1–V8 dependem de validação autenticada em navegador real (desktop/mobile, claro/escuro, teclado/foco, consentimento de substituição CNPJ/person_type, obsolescência de preview, URL/F5/deep link, fallback manual). Não converter verificação estática do bundle em PASS visual. Cenários 403, 429 e falha upstream `INCONCLUSIVE` seguem `TEST_NOT_RUN` no runtime, com testes isolados como evidência complementar.

**Próxima tarefa delimitada:** aceite visual/browser-only em ambiente já publicado, sem rebuild, sem deploy, sem alterações de backend, sem executar criação real de fornecedor. Usar conta autorizada e dados de teste aprovados; não expor tokens/CNPJs em evidência. Registrar screenshots/resultado por cenário e artefato verificado; se impossível autenticar/navegar, manter `INCONCLUSIVE`. R1.S3 `BLOCKED`, S4/S5/S6 não autorizados. Gate ERP de escrita permanece OFF.
