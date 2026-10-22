# X3.FINAL — PROPOSTA de Registro ROPA: Consulta Cadastral Externa de Fornecedores (CNPJ)

**Status:** `PROPOSTA — PENDENTE DE ENDOSSO DPO`  
**Data:** 2026-10-22  
**Elaborado por:** GPT Arquiteto (X3.FINAL)  
**Autoridade competente para aprovação:** Michael Marotto — DPO (ti@delpi.com.br), conforme `docs/13-auditoria-lgpd/ropa-registro-tratamento.md`

> **Aviso:** este documento é uma **proposta** de registro para a operação descrita
> abaixo. Ele **não constitui autorização institucional** nem registro efetivo no
> ROPA. A integração `Portal Suprimentos → supplies-api → external-data-api →
> BrasilAPI` permanece **desabilitada** (`EXTERNAL_DATA_CNPJ_PROVIDER=unavailable`)
> até endosso formal do DPO e/ou incorporação ao ROPA canônico
> (`docs/13-auditoria-lgpd/ropa-registro-tratamento.md`).

---

## Operação proposta — ROPA §10 (texto para revisão do DPO)

| Campo | Detalhe proposto |
|-------|------------------|
| **Operação** | Consulta de dados cadastrais públicos de fornecedores (CNPJ) em fonte externa de terceiros para saneamento cadastral assistido |
| **Fluxo** | Portal Suprimentos (MFE) → `supplies-api` (AuthZ via Core) → `external-data-api` (rede privada, S2S individual) → BrasilAPI CNPJ v1 (dados públicos da Receita Federal) |
| **Dados tratados** | Dados de **pessoa jurídica**: razão social, nome fantasia, CNAE, natureza jurídica, endereço comercial, situação cadastral, porte, data de abertura |
| **Dados pessoais potencialmente presentes na resposta da fonte** | QSA (sócios/administradores — nome + CPF), telefones, e-mail — **excluídos por design**: normalizador não projeta QSA/CPF; campos de contato são forçados a `null` no consumidor **independentemente** do que a fonte retornar; payload bruto nunca é persistido; `source_reference` armazenado em forma sanitizada (`{provider}:cnpj-…{4 dígitos finais}`) |
| **Risco residual de dados pessoais** | CNPJs de empresários individuais/MEI/EIRELI podem identificar pessoa natural (o próprio número e endereço comercial podem ser residenciais). A minimização remove os campos nominalmente pessoais, mas razão social/endereço dessas PJ podem refletir dados do titular-pessoa |
| **Finalidade** | Saneamento e atualização cadastral de fornecedores (SA2/Protheus) com proposta humana obrigatória — a consulta externa **nunca** gera escrita automática; cada diferença exige revisão (S2) e decisão de usuário autorizado; `prepare-update` permanece *draft-only* |
| **Base legal proposta** | Legítimo interesse (Art. 7º, IX) — manutenção da qualidade cadastral de parceiros comerciais com minimização e sem finalidade de perfilamento. **Sujeita a confirmação/deliberação do DPO**, incluindo avaliação de legítimo interesse (LIA) se o DPO entender necessária |
| **Retenção** | Snapshots comparados persistem como propostas de revisão (S2) vinculadas ao ator; trilha de auditoria das decisões mantida. Prazo de retenção das revisões: **a definir pelo DPO** (sugestão: seguir política de auditoria de 2 anos) |
| **Compartilhamento** | Interno apenas (rede privada `delpi-network`). A consulta outbound envia **somente o número CNPJ** à BrasilAPI — nenhum dado pessoal de usuário, nenhum JWT |
| **Medidas técnicas e organizacionais** | (1) Provider fail-closed (`unavailable` por padrão); (2) S2S individual via Keycloak Client Credentials — JWT de usuário nunca é encaminhado; (3) allowlist de consumer = `supplies-api`; (4) rate limit distribuído (consumer/CNPJ/global, Redis dedicado `delpi-redis`, chaves de CNPJ com hash); (5) DTO v1 com allowlist estrita de campos e validação de `source_type=THIRD_PARTY_API`; (6) sem rota pública (porta não publicada); (7) sem logs de payload bruto; (8) rollback por feature flag sem perda de revisões S2 |
| **Operador terceiro** | BrasilAPI (projeto open-source que repassa dados públicos da Receita Federal). A fonte disponibiliza dados **já públicos** — não há fluxo de dados pessoais da DELPI para o operador além do identificador CNPJ consultado |

## O que falta para `GATE-F1 = PASS`

1. **Endosso formal do DPO** desta operação — por uma das vias:
   - a) incorporação da seção acima ao ROPA canônico (`docs/13-auditoria-lgpd/ropa-registro-tratamento.md`) assinada/aprovada pelo DPO; **ou**
   - b) parecer por escrito do DPO dispensando registro adicional com fundamentação (ex.: nenhum dado pessoal tratado após minimização); **ou**
   - c) LIA (avaliação de legítimo interesse) se o DPO entender exigível dado o risco residual de MEI/EI.
2. **Definição de retenção** das revisões S2 com snapshot cadastral.
3. (Opcional, recomendado) Decisão sobre política de consulta a CNPJ de MEI/EI, cujo cadastro pode espelhar dados do titular-pessoa.

## O que falta para `GATE-F2 = PASS`

Identidade de teste explicitamente autorizada:
- usuário de teste no Keycloak produtivo com capability de fornecedores;
- fornecedor/CNPJ de teste autorizado para consulta;
- confirmação de escopo permitido de revisão/decisão.

Nenhuma identidade de teste está documentada em nenhum artefato do repositório.
**Owner da resolução:** Product Owner (credencial/fornecedor autorizado) em conjunto com quem administra o Keycloak/Core.

## Evidência técnica de minimização (verificável no código)

- `external-data-api` — normalizador não projeta QSA/CPF; `contact=null` fixo.
  `external-data-api/app/infrastructure/normalization/brasilapi_cnpj_normalizer.py`
- `supplies-api` — consumer ignora o bloco `contact` mesmo se populado (rework X2,
  commit `36ada077c7`). `supplies-api/app/infrastructure/gateways/external_data_company_registry_provider.py`
- Freeze de contrato: `EXTERNAL-DATA-API-CONTRACT-FREEZE-X0.md`.
