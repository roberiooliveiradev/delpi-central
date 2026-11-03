# 50 — VISTA/TV — ISSUE #129 VISION INVENTORY RECONCILIATION

Data: 2026-11-03 | Corrige doc 49 (declarava vision gap total).

## Inventario corrigido — EXISTING_EQUIVALENT = YES

IMAGE_EVALUATION_OWNER = minha-delpi-ai-api
- ChatDocumentVisionService (application)
- document_vision_runtime.py
- chat_document_vision_vlm_payload_service.py
- chat_document_vision_attachment_service.py
- Pipeline: attachment -> VLM -> findings (desenhos/documentos).

IMAGE_CAPTURE_OWNER = tv-dashboard-presentation/e2e (seeded)
+ public-hub present (palco canonico, exige share token).

## Gap real — nao e capability, e transporte + acesso

| Owner | Estado |
|---|---|
| IMAGE_EVALUATION_OWNER | EXISTE (minha-delpi-ai-api) |
| IMAGE_TRANSPORT_OWNER | GAP — PNG LAB->VLM cross-app sem contrato sancionado |
| IMAGE_CAPTURE_AUTH | AUTHORIZATION_GATE — share token governado ou SSO preview |
| MUTATION_OWNER | tv-dashboard-api (ok) |

## Veredito — ARCHITECTURE_OR_AUTHORIZATION_BLOCKED

A avaliacao visual CANONICA existe no runtime da Minha DELPI AI;
o bloqueador e o caminho sancionado de transporte (boundary:
tv-dashboard-api nao importa dominio de app irmao; contrato de
attachment do chat e o candidato canonico). Decisao: ADR/
aprovacao de contrato de evidence, nao mais codigo.
