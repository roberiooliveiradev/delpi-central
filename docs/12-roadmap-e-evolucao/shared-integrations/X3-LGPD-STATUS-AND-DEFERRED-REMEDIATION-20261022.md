# External Data API / Suprimentos — estado LGPD e adequação posterior (2026-10-22)

> **DECISÃO DE PRIORIZAÇÃO DO PRODUCT OWNER — DOCUMENTED / COMPLIANCE PENDING.** O PO pediu registrar o estado de conformidade atual e planejar o fechamento dos residuais LGPD após comprovar o funcionamento completo da integração. **Não constitui endosso do DPO, mudança de base legal, dispensa de ROPA ou autorização para transgredir requisitos institucionais/legais.** Não classificar pendências como `PASS`; qualquer consulta produtiva continua sujeita às autoridades e gates efetivamente aplicáveis.

## 1. Estado atual verificável nas evidências do projeto

| Item | Estado | Evidência/observação |
|---|---|---|
| Serviço compartilhado `external-data-api` | IMPLEMENTED; runtime técnico reportado PASS | X1; X3 runtime evidence; sem gateway público |
| Consumo S2S `supplies-api → external-data-api` | IMPLEMENTED; S2S Keycloak real reportado PASS | X2/X3; consumer `supplies-api` allowlisted |
| Redis DELPI/limitação distribuída | IMPLEMENTED; health corrigido reportado PASS | X3.FINAL Redis healthcheck |
| Migrations de revisão `V001–V003` | Aplicadas em produção segundo inventário X3 | X3 runtime evidence |
| Fonte externa BrasilAPI em produção | **DESABILITADA** no último inventário | `EXTERNAL_DATA_CNPJ_PROVIDER=unavailable`; não assumir atualização sem nova evidência |
| Smoke CNPJ real e reviews/decisions E2E | **TEST_NOT_RUN / INCONCLUSIVE** | Ausência de autorização institucional comprovada e identidade/fornecedor de teste documentados |
| Autorização do Product Owner | **PROVEN** como decisão de produto | `X3-FINAL-PO-AUTHORIZATION-20261022.md` e decisão desta etapa |
| ROPA geral DELPI | **EXISTE** | `docs/13-auditoria-lgpd/ropa-registro-tratamento.md` (atualização indicada 2026-05-26) |
| Operação específica CNPJ externa no ROPA vigente | **PENDING** | Proposta separada, ainda sem incorporação/parecer comprovado |
| Base legal, análise de necessidade/proporcionalidade e possível LIA | **PENDING** | Legítimo interesse é hipótese proposta, não parecer concluído |
| Retenção de revisões/snapshots e expurgo | **PENDING** | Prazo e operacionalização a confirmar; TTL de revisão não equivale automaticamente a retenção/expurgo |
| MEI/EI e dados potencialmente pessoais | **PENDING** | Razão social/endereço podem remeter a pessoa natural; avaliar tratamento |
| Dados sensíveis e contato | Mitigações em código reportadas | QSA/CPF excluídos; contato forçado a null no service/consumer; verificar no HEAD/runtime quando necessário |

## 2. Decisão de sequenciamento

1. **Etapa técnica:** priorizar evidência de funcionamento completo e controlado do fluxo `supplies-api → external-data-api → BrasilAPI → S1 → S2 → decisões → prepare-update`, sem escrita ERP, com identidade e fornecedor de teste autorizados. Preferir ambiente isolado/testes sintéticos ou execução institucionalmente autorizada. **Não inferir licença para consultar dados reais em produção quando gate institucional aplicável permanece ausente.**
2. **Etapa de adequação LGPD após validação funcional:** consolidar classificação da operação, revisar minimização, definir finalidade/base legal/necessidade, avaliar legítimo interesse e LIA quando aplicável, aprovar incorporação ao ROPA, determinar retenção/expurgo, avaliar MEI/EI, comunicação e fluxo de titulares, e obter decisão documentada do DPO/owner institucional quando exigida.
3. **Liberação final de operação produtiva:** somente após gates técnicos e de conformidade aplicáveis comprovados; não chamar a operação de “LGPD adequada” antes disso. O PO não está delegando ao Cursor autoridade para emitir parecer jurídico/DPO.

Essa sequência reflete prioridade de execução, não dispensa de salvaguardas legais. Se uma verificação institucional independente for necessária **antes** da consulta real, ela continua condição dessa consulta; testes offline e técnicos podem avançar.

## 3. Backlog LGPD posterior (owner proposto: DPO + responsáveis do produto)

- `LGPD-01`: rever e endossar a proposta `X3-FINAL-ROPA-PROPOSAL-EXTERNAL-REGISTRY-20261022.md`, ou emitir decisão fundamentada sobre enquadramento/registro.
- `LGPD-02`: registrar base legal, finalidade e avaliação de necessidade/expectativa dos titulares; deliberar sobre LIA.
- `LGPD-03`: definir retenção real, expurgo e auditoria das revisões/propostas/decisões, diferenciando janela de revisão de obrigação de guarda.
- `LGPD-04`: política de tratamento para MEI/EI e contatos, e eventual capacidade de filtragem; preservar bloqueio de `contact.*` até decisão específica.
- `LGPD-05`: confirmar termos e papel do provedor BrasilAPI, compartilhamento do CNPJ, segurança, logs, direitos dos titulares e revisão periódica.
- `LGPD-06`: anexar evidência de aprovação/conclusão ao ROPA canônico; reexecutar gate LGPD e atualizar documentação do runtime.

## 4. Gating, riscos e escopo

- Estado de conformidade: **INCONCLUSIVE / PENDING**; controles técnicos não representam certificação global LGPD.
- Estado do provider no último runtime comprovado: **unavailable**, não mudar este documento para `brasilapi` sem evidência do ambiente.
- Dados pessoais podem estar presentes em registros públicos, inclusive CNPJ de empresário individual; ausência de CPF/QSA na projeção não elimina toda hipótese de tratamento de dados pessoais.
- Não mudar AuthZ/Core/RBAC, regras SA2, contrato X0, S1/S2, proveniência ERP ou habilitar escrita Protheus.
- Não inserir aprovação fictícia no ROPA, apagar residual ou rotular `PASS` por decisão de priorização.
- Correção documental adicional identificada: `X3-RUNTIME-EVIDENCE-20261022.md` tem adendo X3.FINAL duplicado/incompleto; corrigir em task documental escopada, preservando fatos.

## 5. Authorities/referências

- `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`
- `docs/13-auditoria-lgpd/ropa-registro-tratamento.md`
- `docs/12-roadmap-e-evolucao/shared-integrations/X3-FINAL-ROPA-PROPOSAL-EXTERNAL-REGISTRY-20261022.md`
- `docs/12-roadmap-e-evolucao/shared-integrations/X3-FINAL-PO-AUTHORIZATION-20261022.md`
- `docs/12-roadmap-e-evolucao/shared-integrations/X3-RUNTIME-EVIDENCE-20261022.md`

**Próximo passo:** produzir evidência funcional permitida pelo contexto e depois executar backlog LGPD com o owner competente. Relatar `INCONCLUSIVE` quando consulta produtiva real ou identidade autorizada permanecerem sem prova.
