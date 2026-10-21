# Engenharia — Contrato candidato para Relatórios Metalográficos

> **STATUS: PROPOSED / CONTRACT_NOT_APPROVED / NOT_IMPLEMENTED**  
> Demanda: Helpdesk #1400. Produto consumidor: MFE **Metalografia DELPI** (`metalography`).  
> Referência funcional e visual: HTML recebido do solicitante, conforme [briefing](../../../docs/12-roadmap-e-evolucao/quality/RELATORIO-METALOGRAFICO-CHAMADO-1400.md).  
> **Não adicionar este documento ao índice de rotas ativas até existência do código e testes.**

## 1. Fonte, owner e gates

- Producer **candidato**: API DELPI / Engenharia (preferência do solicitante; validar owner e existência de equivalente).
- Consumer: MFE `metalography`, eventualmente Portal de Engenharia, ainda não implementado.
- Base gateway existente: `/apps/api-delpi`. **Prefixo de domínio proposto**: `/engineering/metallographic-reports`.
- O documento `platform-frontend-mfe-experience.mdc` exige que MFE com API própria não consuma `api-delpi` diretamente. Definir contratualmente se há BFF/adapter próprio antes da implementação; **ARCHITECTURE_DECISION_REQUIRED** para o wiring, sem autorizar bypass da regra.
- `EXISTING_EQUIVALENT=TO_INVENTORY`; `REUSE_DECISION=PENDING`. Inventariar rotas de Engenharia, upload/arquivos, armazenamento, PDF, RBAC e consumidores.
- Sem schema de DB, migration, endpoint real, permissão cadastrada, deploy ou teste criado por este texto.
- Alteração planejada: **ADDITIVE**, condicionada à ausência de colisão e à compatibilidade comprovada.

## 2. Rota e identidade HTTP propostas

Prefixo completo via gateway: `/apps/api-delpi/engineering/metallographic-reports`. `{report_id}` é UUID e **não** é número humano de relatório. `{slot}` assume `original` ou `measured`.

| Método | Sufixo | operationId proposto | Permissão candidata | Resultado |
|---|---|---|---|---|
| POST | `/` | `engineering_create_metallographic_report` | `metalography.create` | 201 + Report |
| GET | `/` | `engineering_list_metallographic_reports` | `metalography.view` | 200 + Page |
| GET | `/{report_id}` | `engineering_get_metallographic_report` | `metalography.view` | 200 + Report |
| PATCH | `/{report_id}` | `engineering_update_metallographic_report` | `metalography.edit` | 200 + Report |
| DELETE | `/{report_id}` | `engineering_delete_metallographic_report` | `metalography.delete` | 204 |
| POST | `/{report_id}/copies` | `engineering_copy_metallographic_report` | `metalography.create` | 201 + Report |
| PUT | `/{report_id}/images/{slot}` | `engineering_put_metallographic_image` | `metalography.edit` | 200 + Image |
| GET | `/{report_id}/images/{slot}` | `engineering_get_metallographic_image` | `metalography.view` | 200 + image binary |
| DELETE | `/{report_id}/images/{slot}` | `engineering_delete_metallographic_image` | `metalography.edit` | 204 |
| GET | `/{report_id}/pdf` | `engineering_export_metallographic_report_pdf` | `metalography.export` | 200 + PDF binary |

Operações, `operationId`, permissions e paths **candidatos**; formalizar em OpenAPI antes de implementar, seguindo regras de nomenclatura e unicidade. Não inferir que qualquer permissão já existe.

## 3. Modelo de dados HTTP v1 (proposta)

`Report` (serializado em JSON):

```json
{
  "id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
  "report_number": "MET-2026-000001",
  "report_date": "2026-10-21",
  "revision": "00",
  "sample": {
    "terminal_code": "TERMINAL-EXEMPLO",
    "terminal_part_number": "PN-EXEMPLO",
    "product_harness": "CHICOTE-EXEMPLO / REV A",
    "cable": "CABO-EXEMPLO",
    "conductor_section": "0.75 mm2",
    "applicator_tool": "APLICADOR-EXEMPLO",
    "press_equipment": "PRENSA-EXEMPLO",
    "batch_production_order": "OP-EXEMPLO",
    "sample_identification": "AMOSTRA-01"
  },
  "measurements": {
    "crimp_height_ch": {"criterion": "A DEFINIR", "measured": "1.20"},
    "crimp_width_cb": {"criterion": "A DEFINIR", "measured": "2.10"},
    "void_area_av": {"criterion": "A DEFINIR", "measured": "4.5"},
    "left_burr_gh_e": {"criterion": "A DEFINIR", "measured": "0.08"},
    "right_burr_gh_d": {"criterion": "A DEFINIR", "measured": "0.07"}
  },
  "conclusion": {"result": "conforming", "notes": "Texto de exemplo"},
  "analyst": {"name": "Analista de exemplo", "user_id": null},
  "images": {
    "original": {"present": false, "content_type": null, "sha256": null},
    "measured": {"present": false, "content_type": null, "sha256": null}
  },
  "status": "draft",
  "version": 1,
  "created_at": "2026-10-21T14:00:00-03:00",
  "updated_at": "2026-10-21T14:00:00-03:00",
  "created_by": "identity-sub",
  "updated_by": "identity-sub"
}
```

Valores são **exemplos ilustrativos, não dados reais de amostra**. `report_number` é atribuído pelo servidor. `id`, `version` e timestamps são server-owned. `measurements.*.criterion` mantém texto de tolerância tal como o HTML; `measured` é string decimal para não perder precisão nem obrigar expressão matemática prematura. Unidades técnicas do layout: CH/CB/GH em mm; AV em %. Regras de normalização, intervalos e obrigatoriedade serão validadas com Engenharia. **Nenhum critério é calculado ou declarado aprovado automaticamente pela API.**

Campos de entrada em POST: `report_date`, `revision`, `sample`, `measurements`, `conclusion`, `analyst` e opcionalmente `status=draft`; sem `id`, `report_number`, imagens binárias, autoria ou timestamps do cliente. Campos vazios são permitidos em rascunho somente conforme matriz de validação aprovada. A revisão técnica do documento não equivale à versão de concorrência `version`.

**PATCH**: parcial sobre campos editáveis, mantendo os demais intactos; não aceita alteração de identidade server-owned nem de imagens por JSON; `null` significa limpar campo somente onde explicitamente permitido pelo schema. Na implementação, formalizar `additionalProperties: false`/equivalente, enums e limites de tamanho.

**Status**: `draft` é o único estado funcional requerido para v1; fluxos de aprovação, assinatura e publicação/versões finais precisam de decisão de domínio antes de serem implementados. `conclusion.result` pode ser `conforming`, `nonconforming` ou `null` em rascunhos.

## 4. Listagem, filtros e paginação

`GET /` com `page` (1-based, default 1), `page_size` (default 20, max proposto 100), `sort` allowlist (`created_at_desc`, `created_at_asc`, `report_date_desc`, `report_number_asc`), `report_date_from`, `report_date_to`, `terminal_code`, `terminal_part_number`, `product_harness`, `cable`, `conductor_section`, `applicator_tool`, `press_equipment`, `batch_production_order`, `sample_identification`, `conclusion_result`. Filtros combinam por AND e respeitam escopo autorizado. Semântica de pesquisa textual (contains, exata, casefold), datas sem valor e exclusões: **a aprovar**. Proposta `Page`:

```json
{"items":[],"page":1,"page_size":20,"total":0,"has_next":false}
```

Ordenação estável acrescenta `id` como desempate; nunca retornar lote sem limite. Evitar vazamento de relatório de outro escopo tanto em lista quanto em GET direto.

## 5. Upload e recuperação de imagens

- `PUT /{report_id}/images/{slot}`: `multipart/form-data` com parte `file`. Tipos candidatos `image/jpeg`, `image/png`; tamanho máximo **a aprovar** com infraestrutura. Decodificar/verificar magic bytes, dimensões, tamanho e integridade. Strip de metadados sensíveis quando aplicável. Processar recorte/centralização no editor e persistir versão final renderizada, preservando original somente se regra de negócio exigir.
- Resposta `Image`: `slot`, `content_type`, `size_bytes`, `sha256`, `version`, `updated_at`; sem URL pública permanente.
- `GET /{report_id}/images/{slot}`: stream binário autenticado e autorizado, `Content-Type` correto, `ETag` e `Cache-Control: private` apropriado; respostas negadas não revelam dados.
- Substituição e exclusão verificam a versão do relatório por `If-Match`, do mesmo modo que PATCH/DELETE; mudança de imagem incrementa `version`. `404` quando slot não existe; `409/412` para conflito/precondition conforme decisão final de contrato.
- Salvar imagem e metadados de forma consistente; estratégia de limpeza de arquivo órfão, backup e retenção é gate técnico, não decisão presumida.

## 6. Concorrência, idempotência e exclusão

- `ETag` representa `Report.version`; exigir `If-Match` em PATCH, DELETE e mutações de imagem. Ausência `428 Precondition Required`; versão divergente `412 Precondition Failed`. Versão mantida e incrementada no servidor.
- `POST /` e `POST /copies` exigem `Idempotency-Key`, com deduplicação atômica escopada por sujeito/operação e request hash, retenção definida pela infraestrutura. Replay idêntico retorna o mesmo recurso; chave reutilizada com payload divergente retorna 409. Não gerar dois números por retries.
- `DELETE` realiza **exclusão lógica** auditada, sem destruição física imediata de registros/imagens; política de retenção/restauração deve ser validada. Excluir novamente com mesmo pedido idempotente não produz novo efeito; GET/lista excluem registros deletados.
- A operação de cópia duplica os dados técnicos e as referências/conteúdo das imagens de forma segura, gera novo ID, número, autoria e revisão inicial a validar; não copia estado de aprovação nem assinaturas.

## 7. PDF técnico e download

`GET /{report_id}/pdf` retorna `application/pdf` e `Content-Disposition: attachment; filename="metalografia-<numero>.pdf"`, com autorização de leitura/exportação e snapshot consistente do relatório já persistido. Preserva visual, seção A4, imagens e cotas do HTML fornecido. Não grava aprovação, não muda status/revisão nem escreve dados silenciosamente. Definir se `draft` pode ser exportado com marca d'água depois de validação do owner; opção padrão proposta é permitir exportação de rascunho **identificado** sem sugerir laudo oficialmente aprovado. Render/timeout/limites e tratamento de falhas devem ser contratados; testes fazem comparação visual amostral.

## 8. Segurança e modelo de erro

JWT Keycloak validado pelo middleware vigente; autorização efetiva via Core/RBAC e escopo de domínio, fail-closed. Permissões `metalography.view|create|edit|delete|export` são **propostas**, não cadastradas. `created_by` e `updated_by` vêm exclusivamente da identidade verificada. Nunca aceitar user_id enviado como autoridade; não autorizar leitura por conhecer UUID. CORS, tamanho de payload, rate limits e auditoria conforme stack aprovada.

Envelope **candidato** para erros de domínio (reconciliar com `api-delpi-response-contract.mdc` e handlers existentes antes do freeze):

```json
{"error":{"code":"REPORT_VERSION_CONFLICT","message":"O relatório foi alterado por outra pessoa.","correlation_id":"request-id"}}
```

| HTTP | Situação |
|---|---|
| 400 | formato incorreto, filtro inconsistente |
| 401 | não autenticado |
| 403 | sem permissão/escopo |
| 404 | relatório, imagem ou recurso indisponível |
| 409 | duplicação de chave ou regra de conflito |
| 412 | `If-Match` não corresponde |
| 413 | imagem/payload acima do limite |
| 415 | mídia não suportada |
| 422 | validação semântica |
| 428 | precondition exigida |
| 429 | limite de requisições |
| 500/503/504 | erro interno, storage/downstream indisponível/timeout |

Não revelar path físico, stacktrace, SQL, token ou segredo. Correlation ID e auditoria sem dados sensíveis desnecessários.

## 9. Compatibilidade, observabilidade e recovery

- Contrato inicial **aditivo** condicionado ao inventário e CI; versionar em OpenAPI oficial; operationIds explícitos e únicos no FastAPI.
- Registrar request/correlation ID, operação, sujeito autenticado, recurso, resultado, latência, erros e eventos de criação, edição, exclusão, cópia, imagem e exportação; sem logar binários nem observações em texto integral.
- Timeout em IO, limites de upload/render PDF, recuperação de objetos órfãos, trilha de auditoria; storage e PostgreSQL somente após verificação dos padrões de Engenharia.
- Migração: não importar registros IndexedDB/localStorage automaticamente. Rollback de aplicação preserva banco e arquivos, sem drop/truncate; migrations expand-first, rollback/roll-forward aprovado.
- Integração futura com Portal de Engenharia deve consumir o mesmo contrato sem duplicar dados.

## 10. Acceptance / Contract gates

1. Criar → consultar → atualizar → listar em outra sessão; campos preservados sem perda.
2. Cada um dos cinco parâmetros e as duas micrografias faz round-trip.
3. Repetir POST com chave igual resulta em **um** relatório; payload diferente com mesma chave é conflito.
4. Duas atualizações concorrentes não silenciam edição anterior; `If-Match` stale é rejeitado.
5. Negar acesso sem JWT/permissão e impedir IDOR cross-user/cross-scope.
6. Upload inválido, excedente, arquivo malformado e slot inexistente têm erros determinísticos.
7. Excluir oculta sem perder auditoria; copiar não altera original.
8. PDF exporta o mesmo snapshot persistido sem mutação; verificar visual vs referência HTML.
9. Filtros/paginação/ordenação preservam a semântica, inclusive zero resultados.
10. Testar OpenAPI, operationId, segurança, schema e status codes, suíte backend, client/BFF/MFE, integração no Portal, mobile/a11y e CI.
11. Validar documentação, README, índice de endpoints **somente após implementação**, migrations e ledger factual, deploy e smoke real quando autorizados.

**STOP CONDITIONS:** owner real conflitante; equivalente existente; decisão BFF/direct API sem resolução; permissão/dados sem contrato; schema de Engenharia indefinido; geração PDF diferente do HTML sem aceite; retenção/upload sem segurança aprovada. **Não executar implementação apenas a partir desta proposta.**
