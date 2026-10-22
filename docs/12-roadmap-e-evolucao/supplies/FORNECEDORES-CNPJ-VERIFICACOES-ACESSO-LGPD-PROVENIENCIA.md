# Verificações restantes — CNPJ, contrato de acesso, mapeamento, LGPD e proveniência

> **Verificado em fontes públicas e contratos internos em 2026-10-21.** Estado: **DOCUMENTED / NOT FROZEN / NO IMPLEMENTATION**. A consulta pública de documentação **não demonstra** credenciais, contrato comercial aceito, dados reais, direito de reuso nem conclusão jurídica da DELPI. Documento complementar ao inventário [fontes oficiais](./FORNECEDORES-CNPJ-INVENTARIO-FONTES-OFICIAIS.md), ao [backend de enrichment](./FORNECEDORES-ENRIQUECIMENTO-CADASTRAL-BACKEND-TECHNICAL-CONTRACT.md) e ao [contrato transversal api-delpi](../../../api-delpi/docs/integrations/supplier-write-provenance-contract-proposal.md) (path relativo deve ser validado).

## 1. Contrato de acesso — fatos oficiais × lacunas

**Serpro Consulta CNPJ (PJ):** o serviço GOV.BR consultado informa contratação online pela Loja Serpro, acesso do contratante na Área do Cliente e requisito de e-CNPJ; após contratação obtêm-se **Consumer Key/Consumer Secret** em Gestão de Chaves. O preço depende de modalidade e volume; a página informa demonstração até 30 dias ou 3.000 consultas, sujeita às condições e cobrança quando excedidas. Modalidades básicas/QSA/Empresa possuem dados e exposição diferentes. **Isso verifica a existência da oferta comercial, NÃO que a DELPI tenha assinatura ou credenciais.**

Referência oficial: https://www.gov.br/pt-br/servicos/obter-solucao-de-consulta-de-dados-do-cadastro-nacional-de-pessoas-juridicas-cnpj (última modificação reportada pelo site: 15/12/2025).

**Conecta gov.br:** o catálogo lista CNPJ (Básica/Empresa/QSA), versão 2.0.2 e acesso para órgãos públicos federal/estadual, com onboarding/firewall/credenciais para órgão. Não é alternativa aberta comprovada a PJ privada. https://www.gov.br/conecta/catalogo/apis/consulta-cnpj e https://www.gov.br/conecta/catalogo/apis/consulta-cnpj/swagger_api_cnpj.md/swagger_view

**REDESIM/consulta pública:** interface web pública de consulta humana não é contrato de robô/API. Sem scraping.

**Estado de acesso na DELPI:** `CONTRACT_SIGNED = TO_INVENTORY`; `PLAN_SELECTED = TO_INVENTORY`; `CONSUMER_CREDENTIALS = NOT_VERIFIED`; `AUTHENTICATED_SANDBOX_RESPONSE = TEST_NOT_RUN`. Só Compras/Jurídico/Segurança podem aprovar contratação/custos/chaves; não solicitamos nem usamos segredos.

## 2. Contrato técnico real (não confundir API Conecta e Serpro contratado)

**PROVEN por documentação oficial:** o catálogo Conecta descreve API CNPJ 2.0.2 com identificador de 14 dígitos, nome empresarial, fantasia, situação, matriz/filial, CNAE/endereço e modalidades Básica/Empresa/QSA; swagger oficial é **referência de esquema de outra oferta/credencial**, não prova que a modalidade Serpro PJ retorne exatamente o mesmo JSON. O site Serpro GOV.BR define por família: Básica (situação, endereço, atividade, natureza, telefone), QSA (mais quadro societário e Simples/MEI), Empresa (inclui dados societários e identificação de sócios).

**Não comprovados:** URL autorizada Serpro PJ, versão de SDK/Swagger contratado, exact JSON, HTTP status, scopes, sandbox, key rotation, rate limit real, SLA, latency e condição jurídica de armazenamento/reexibição. Portanto **não definir DTO executável nem provider adapter como FROZEN**.

Gate de prova futura: manual técnico efetivamente acessível ao contratante + payload sanitizado de homologação + respostas 200, 404/no-hit, 429, 5xx, autenticação expirada e limites contratuais. Não coletar CPF de QSA no MVP.

## 3. Mapeamento fornecedor SA2: evidência do contrato existente

Fonte interna: `api-delpi/docs/integrations/protheus-rest-supplier-post-field-matrix.md` no HEAD da branch documental; esta matriz documenta limites SA2 (ex. `A2_NOME C(50)`, `A2_NREDUZ C(20)`, `A2_END C(40)`, `A2_BAIRRO C(20)`, `A2_CEP C(8)`, `A2_MUN C(25)`, `A2_COD_MUN C(5)`, `A2_EST C(2)`, `A2_TEL C(50)`, `A2_EMAIL C(50)`). Para PUT consta nome/fantasia e outros campos por decisão de PO **com homologação TOTVS pendente**; documento fiscal `tax_id` protegido. Contrato REST upstream documentado em `api-delpi/docs/integrations/protheus-rest-supplier-api-contract.md`.

| Fonte CNPJ (candidata) | Destino SA2 | Decisão de mapeamento | Pode entrar em aceite em lote agora? |
|---|---|---|---|
| nome empresarial | `supplier_name A2_NOME` | comparar; nome 150 externo pode exceder C(50): bloquear truncamento e exigir revisão | **NÃO** até provider/PUT real verificados |
| fantasia | `supplier_short_name A2_NREDUZ` | fantasia não necessariamente equivale a abreviação; review manual | **NÃO** |
| logradouro/tipo/número/complemento | `address A2_END` | composição C(40), endereço do estabelecimento ≠ entrega, revisão manual | **NÃO** |
| bairro | `district A2_BAIRRO` | C(20), acento/case conforme domínio; fonte vazia não limpa ERP | **NÃO** |
| CEP | `postal_code A2_CEP` | 8 dígitos, identidade de estabelecimento/branch | **NÃO** |
| município/UF/IBGE | `city A2_MUN`, `state A2_EST`, `city_code A2_COD_MUN` | trio dependente, reconciliação CC2 específica, nunca IBGE→CC2 direto | **NÃO** |
| telefone, e-mail | `A2_TEL`, `A2_EMAIL` | contato público não prova canal operacional atual, manual | **NÃO** |
| CNPJ | `A2_CGC` | confirmar identidade da entidade e filial, **nunca atualizar por sugestão** | **NUNCA** |
| status, CNAE, QSA, natureza jurídica | sem campo PUT equiv. comprovado | exibir info autorizado, sem proposta de gravação | **NUNCA sem novo contrato** |
| financeiro, contábil, compras | sem fonte equivalente legitimada | interno; protegido contra enriquecimento externo | **NÃO** |

Resultado: `FIELD_CANDIDATES_MAPPED_DOCUMENTALLY=YES`, `FIELDS_VERIFIED_ELIGIBLE_FOR_BULK_PUT=ZERO`. Não confundir critério de comparação com autorização de gravar.

## 4. LGPD, segurança e retenção — exigências confirmadas e política proposta

A ANPD publica orientação sobre **legítimo interesse**, cuja avaliação envolve finalidade, necessidade, balanceamento e salvaguardas. **Não é possível declarar legítimo interesse automaticamente** só porque CNPJ é público; DPO deve determinar base legal e papéis do tratamento, incluindo contato de pessoa natural, representante/CPF e dados de sócios. Fonte: https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-lanca-guia-orientativo-sobre-legitimo-interesse e https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia_orientativo_hipoteses_legais_tratamento_de_dados_pessoais_legitimo_interesse

**Proposta de classificação e retenção por categoria (NÃO prazo legal):**
- resposta bruta Serpro: **não persistir** no MVP, salvo permissão contratual expressa, justificativa e controles;
- valor proposto em review: guardar somente campos aprovados/necessários, cifrados quando pessoais, com `review_expires_at` configurável (exemplo de 24h **não aprovado**);
- decisão aceite/recusa por campo: registrar evento com `actor_subject`, `source_id`, referência de evidência, decisão, timestamp, sem payload integral; retenção de auditoria com prazo definido e aprovado pelo jurídico/DPO, **PENDING**;
- gravação `api-delpi`: trilha de proveniência por campo + status ERP, período compatível com finalidade, obrigação aplicável e reconciliação, **não prazo arbitrário**;
- logs operacionais: request/correlation/status e contagem, sem PII/endereços/CNPJ completo/tokens;
- chaves criptográficas em secret manager autorizado, acesso separado por finalidade, exclusão/anonimização sob política aprovada, trilha de acessos.

**Privacidade visível ao usuário:** exibir origem e modo de atualização por campo, instante da consulta, instante da alteração e status `CONFIRMED`/não-confirmado; nome do operador somente para usuários com visibilidade autorizada. Sem declarar `Serpro` se dado foi digitado manualmente.

**Pendências jurídicas:** base legal por categoria, finalidade, controlador/operador, contrato/DPA com Serpro, retenção e descarte, resposta a titulares, transferências, RIPD quando aplicável, política de exibição de autor/PII, obrigação de logs. **LGPD_GATE=PENDING LEGAL REVIEW**.

## 5. Proveniência obrigatória — impacto nos dois contratos

**Pedido PO transformado em requisito de contrato:** uma informação escrita por qualquer consumidor autorizado da api-delpi precisa carregar **origem e modo por campo**; não basta auditar que houve PUT. Uma operação pode combinar 2 campos da fonte oficial com 1 campo manual.

Exemplos de exibição após **persistência confirmada**:
- `Razão social — Origem: API governamental [Serpro somente se provado] · Modo: sugestão aceita pelo usuário · Alterada em ...`
- `Bairro — Origem: formulário manual · Modo: edição direta · Alterada em ...`
- `Endereço — Origem: integração interna autorizada · Modo: sincronização de sistema · Política: ...`
- Caso `ACKNOWLEDGED/UNKNOWN`: **não exibir “atualizado”**; apresentar “envio realizado; confirmação pendente”.

Ver contrato [`api-delpi/docs/integrations/supplier-write-provenance-contract-proposal.md`](https://github.com/roberiooliveiradev/delpi-central/blob/docs/supplies-supplier-data-enrichment-decision-flow-20261021/api-delpi/docs/integrations/supplier-write-provenance-contract-proposal.md) para enum de `source_type`, `change_mode`, campos de metadata, audit store central, estados e compatibilidade multi-consumer. A `supplies-api` registra aceite/recusa de proposta; a `api-delpi` registra metadados canônicos da tentativa/resultado de gravação provenientes de **todos os BFFs**, sem adicionar campos desconhecidos à MATA020/SA2. É preciso inventariar consumidores atuais de PUT e cobertura de alterações feitas **fora** da api-delpi; não prometer trilha completa dessas alterações.

## 6. Ledger de conclusão das verificações

| Verificação | Resultado | Evidência pendente |
|---|---|---|
| Oferta comercial para PJ | `PROVEN (public documentation)` | assinatura DELPI, plano, custo e termo |
| Requisito e-CNPJ e Consumer Key/Secret | `PROVEN (public documentation)` | credenciais DELPI nunca pedidas/exibidas |
| Contrato JSON Serpro PJ exato | `TO_INVENTORY` | manual contratado / payload de teste autorizado |
| Conecta gov.br destinado a órgãos públicos | `PROVEN (public documentation)` | concessão DELPI não demonstrada; não usar |
| Mapping candidatos para SA2 | `PROVEN (internal documentation)` | provider real e PUT allowlist/upstream |
| LGPD legítimo interesse exige teste/avaliação | `PROVEN (ANPD guidance)` | decisão jurídica da DELPI |
| Prazo de retenção reviews/decisões/provenance | `PENDING` | DPO e política corporativa |
| Origin/mode por campo cross-consumer | `TARGET (PO REQUIRED)` | inventory integration tracking, API contract, migrations |
| Visibilidade da origem ao usuário após confirmação | `TARGET (PO REQUIRED)` | AuthZ e API de histórico |
| Cobertura de gravações fora da api-delpi | `TO_INVENTORY` | TOTVS hooks/events/writers |

**Sem GO de implementação.** Ações necessárias fora desta execução: proprietário contrata/autoriza acesso Serpro; jurídico/DPO aprova tratamento e retenção; arquitetura inventaria POST/PUT real e outros consumers; Product decide prazos e motivos; após isso freeze/ADR/OpenAPI e aprovação de implementação por etapa.
