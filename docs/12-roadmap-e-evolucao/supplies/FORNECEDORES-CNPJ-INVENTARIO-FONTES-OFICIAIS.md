# Inventário de fontes oficiais CNPJ — enriquecimento assistido de fornecedores

> **Inventário documental pesquisado em 2026-10-21; sem implementação ou acesso contratado.** Escopo de fornecedores SA2, condicionado a confirmar a expressão "clientes" com o PO. `PROVEN` refere-se a **conteúdo documental de fontes oficiais**, NÃO à disponibilidade de credenciais, direito de integração, execução de chamada real, qualidade de dados por CNPJ nem compatibilidade runtime DELPI. `TO_INVENTORY` significa informação ausente ou pendente de validação com owner/fornecedor.
>
> Vinculado a [fluxo](./FORNECEDORES-ENRIQUECIMENTO-CADASTRAL-FLUXO-CONTRATO.md), [backend técnico](./FORNECEDORES-ENRIQUECIMENTO-CADASTRAL-BACKEND-TECHNICAL-CONTRACT.md) e [UX](./FORNECEDORES-ENRIQUECIMENTO-CADASTRAL-FRONTEND-UX-CONTRACT.md). Este documento não autoriza criação de adapters, dados, deploy, jobs nem PUT.

## 1. Fontes pesquisadas e elegibilidade

| Fonte | Natureza | Acesso de empresa privada | Atualização/cobertura | Resultado do inventário |
|---|---|---|---|---|
| **Serpro Consulta CNPJ (serviço de contratação para pessoa jurídica)** | Integração API comercial com dados da Receita Federal | **Contratação online para PJ**, certificado e-CNPJ, Consumer Key/Secret; cobrança por volume/tipo, demonstração sujeita a condições | Página de serviço descreve consulta online e tempo real à base da RFB; SLAs, preço concreto e payload contratado dependem de plano/manual | **CANDIDATE PRIORITÁRIO** para consulta síncrona sob demanda; **NO ACCESS PROVEN** |
| **Conecta gov.br — CNPJ Básica / Empresa / QSA** | Catálogo governamental API 2.0.2 | Página orienta acesso a **órgãos públicos**, não prova elegibilidade da DELPI (empresa privada). Não usar endpoints públicos documentados sem credenciais/autorização | Swagger oficial especifica campos estruturados e endpoints, versão 2.0.2 | **REFERÊNCIA DE SCHEMA**, **NOT APPROVED CONSUMER** para DELPI |
| **Receita Federal/REDESIM — Consultar CNPJ e comprovante** | Portal público de consulta humana | Serviço público disponível a qualquer pessoa, mas **não há neste inventário contrato de API aberta para scraping/automação** | Comprovante e situação cadastral; resultado por consulta pública | **VALIDAÇÃO HUMANA/REFERÊNCIA**, não adapter automático |
| **RFB — dados públicos/abertos do CNPJ** | Dados para download, não API transacional por registro | Acessibilidade e condições específicas do conjunto devem ser revistas; documentação geral de dados abertos confirma formatos estruturados | Snapshot em arquivos; periodicidade, layout e versão do conjunto CNPJ específico ainda **TO_INVENTORY** | **OPÇÃO FUTURA DE INGESTÃO**, não adequada presumidamente a consulta síncrona; vedado criar cópia local sem governança |
| **BrasilAPI e agregadores privados de CNPJ** | Terceiros não governamentais | Licença, fonte, disponibilidade, atualização, quotas e PII variam; não foram habilitados/aprovados neste inventário | Não assumir atualização oficial em tempo real | **FORA DO PRIMEIRO GATE**, reavaliar se Serpro inviável |
| **Serviço de CEP da api-delpi** | Busca geográfica compartilhada já relatada no projeto | Não é fonte de identidade empresarial | Rua/bairro/município por CEP, com possibilidade de endereço geral | **AUXILIAR**, não identifica endereço específico do estabelecimento nem substitui CNPJ |

### Fontes oficiais e referências verificadas (links consultados)

1. Gov.br: Serviço para obter solução digital de consulta CNPJ, Serpro; requisitos de contratação, e-CNPJ, chave/secret, condições comerciais e teste. https://www.gov.br/pt-br/servicos/obter-solucao-de-consulta-de-dados-do-cadastro-nacional-de-pessoas-juridicas-cnpj
2. Conecta gov.br: catálogo API CNPJ Básica / Empresa / QSA, indicação de acesso para órgãos públicos e requisitos de adesão. https://www.gov.br/conecta/catalogo/apis/consulta-cnpj
3. Swagger oficial da API Conecta CNPJ v2.0.2, atributos, nomes e esquema de resposta. https://www.gov.br/conecta/catalogo/apis/consulta-cnpj/swagger_api_cnpj.md/swagger_view
4. Gov.br: Serviço Consultar CNPJ, canais REDESIM/comprovante, disponível a qualquer pessoa **via canal de consulta**, não prova API automatizável. https://www.gov.br/pt-br/servicos/consultar-cadastro-nacional-de-pessoas-juridicas
5. REDESIM: página de emissão de comprovantes. https://www.gov.br/empresas-e-negocios/pt-br/redesim/comprovantes/
6. Receita Federal: Dados Abertos e Cadastros CNPJ. https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/dados-abertos/cadastros
7. Receita Federal: repositório de dados abertos (formatos aceitos, NÃO prova cadência do conjunto CNPJ). https://www.gov.br/receitafederal/dados

## 2. Campos externos verificáveis em contratos oficiais

O **Swagger do Conecta** é evidência documental de um formato de consulta oficial; **não é prova de que a API comercial do Serpro possua campo exatamente idêntico**, nem que nosso plano possa acessá-los. Antes de congelar mapping da DELPI, obter **manual, versão, contrato efetivamente adquirido e payload de teste permitido**.

| Atributo em fonte governamental | Estrutura no schema de referência | Potencial campo supplier/SA2 | Classificação para MVP |
|---|---|---|---|
| Identificador CNPJ 14 dígitos | `ni` | `tax_id`/`A2_CGC` | **IDENTITY ONLY / PROTECTED**; nunca atualizar |
| Nome empresarial | `nomeEmpresarial` | `supplier_name`/`A2_NOME` | Comparável, potencialmente aplicável **somente** após limite SX3 e PUT elegível |
| Nome fantasia | `nomeFantasia` (contrato exibe variação de grafia `nomefantasia`) | `supplier_short_name`/`A2_NREDUZ` | **MANUAL REVIEW**: fantasia não é necessariamente abreviação interna; não aceitar em lote inicialmente |
| Situação e data | `situacaoCadastral.codigo/data/motivo` | Nenhum PUT genérico | **INFORMATIVO / ALERTA**; não confundir com status ativo de fornecedor |
| Natureza jurídica | `naturezaJuridica.codigo/descricao` | Sem correspondência SA2 comprovada | **INFORMATIVO** |
| Data de abertura | `dataAbertura` | Sem correspondente validado | **INFORMATIVO** |
| CNAE principal/secundários | `cnaePrincipal`, `cnaeSecundarias` | Sem correspondente validado | **INFORMATIVO** |
| Logradouro e tipo | `endereco.tipoLogradouro/logradouro` | `address`/`A2_END` | **MANUAL REVIEW**: número+complemento e comprimento SX3; sem truncar |
| Número/complemento | `endereco.numero/complemento` | Pode compor `A2_END`, contrato SA2 precisa confirmar | **MANUAL REVIEW**, não sobrescrever sem transformação segura |
| Bairro | `endereco.bairro` | `district`/`A2_BAIRRO` | Candidato comparável, aplicar só após validação de campo e elegibilidade |
| CEP | `endereco.cep` | `postal_code`/`A2_CEP` | Candidato comparável, 8 dígitos |
| Município/UF | `endereco.municipio.codigo/descricao`, `endereco.uf` | `city`, `city_code`, `state` / `A2_MUN`, `A2_COD_MUN`, `A2_EST` | **DEPENDENCY GROUP**; CC2 e UF obrigatórios; não copiar IBGE diretamente |
| País | `endereco.pais.codigo/descricao` | `A2_PAIS` e `A2_CODPAIS` têm catálogos diferentes | **NOT AUTO-COMPARABLE** até regra explícita |
| Telefone | `telefone[].ddd/numero` | `area_code`, `phone` | **MANUAL REVIEW**: pode conter múltiplos e ser contato público desatualizado |
| E-mail | `correioEletronico` | `email`/`A2_EMAIL` | **MANUAL REVIEW**, não substituir contatos operacionais sem política |
| Capital social, porte, regimes tributários | campos estruturados no Swagger | Nenhum PUT seguro comprovado | **INFORMATIVO** |
| QSA / representante, CPF | `socios[]`, `representanteLegal` | Nenhum campo de contato equivalente | **FORA DO MVP / DATA MINIMIZATION**; evitar coletar CPF |
| Condições, natureza financeira, contas contábeis, pagamento | não demonstrados como campos equivalentes no schema CNPJ | `A2_COND`, `A2_NATUREZ`, `A2_CONTA`, `A2_FORMPAG` | **INTERNAL / NEVER AUTO-PROPOSE** |

### Regras de comparação específicas

- Provedor não informou atributo: `SOURCE_MISSING`, jamais sugerir limpar SA2.
- Provedor retornou atributo com limite maior que SX3: `PENDING_VALIDATION`; não truncar silenciosamente.
- Dado externo pode estar correto no CNPJ e inadequado para operações DELPI; divergência não equivale a erro do cadastro.
- Endereço do CNPJ refere-se ao **estabelecimento da inscrição**, não prova endereço de entregas, faturamento ou contato operacional; exigir avaliação.
- Validar CNPJ/filial exatos do fornecedor, não mapear registro da matriz para filial.
- Dados de contato podem ser de contador/terceiro; não assumir titularidade.
- Mesmo quando campo é comparável, elegibilidade PUT depende de regras vigentes e gates independentes do review.

## 3. Recomendação de arquitetura e decisão de fonte

**Recomendação condicional:** priorizar negociação/avaliação de **Serpro Consulta CNPJ para empresas** como eventual provider síncrono oficial no fluxo sob demanda; não iniciar integração sem contratação, aprovação de segurança, avaliação da documentação de campos e teste com credencial corporativa.

**Não aprovar Conecta gov.br** para integração privada com base apenas em sua documentação pública: seus endpoints e swagger não concedem acesso a DELPI. Não substituir contratação por scraping do portal REDESIM/Receita.

**Alternativa futura:** dados abertos CNPJ exigem avaliação específica de cadência, volume, formato, qualidade, infraestrutura, governança, dados pessoais e owner corporativo; não copiar base inteira no Postgres `supplies` por conveniência.

**Política de fallback:** não misturar silenciosamente payloads de provedores com diferentes versões/recências. Se houver fallback futuro, expor `source_id`, `retrieved_at`, `coverage`, `source_reference_date`, `licensing` e resolução de conflitos por campo; impedir proposta elegível quando fontes não comparáveis.

## 4. Escopo de MVP recomendado após GATE

1. Consulta iniciada pelo usuário a partir do CNPJ já cadastrado em SA2, com AuthZ Core no BFF.
2. Exibir identificação, nome empresarial, endereço completo e CEP; nome fantasia e contato como revisão manual/condicional.
3. Exibir situação cadastral, CNAE, data de abertura e natureza jurídica somente como informação (sem PUT).
4. Comparar cada campo com snapshot canônico do `api-delpi`, distinguir `MATCH`, `DIFFERENT`, `SOURCE_MISSING`, `PENDING_VALIDATION`, `PROTECTED`.
5. Decisão individual ou lote apenas nas propostas mapeadas, editáveis e pendentes. Com gate write OFF, nenhuma persistência ERP.
6. Restringir chamadas externas a CNPJ já associado ao fornecedor, sem API genérica de enumerar CNPJs.
7. Relatar "consulta não disponível" quando credencial/contratação não existir; não fingir integração real.

## 5. Pendências para transformar em contrato FROZEN

| Gate | Evidência necessária | Owner sugerido | Estado |
|---|---|---|---|
| SRC-01 | Contrato/plano Serpro disponível para PJ da DELPI, preços, limites, finalidade permitida | Produto / compras / jurídico | `TO_INVENTORY` |
| SRC-02 | Manual técnico vigente da **API contratável**, amostra sanitizada, versão, auth, payload fields, SLAs e rate limits | Integrações / api owner | `TO_INVENTORY` |
| SRC-03 | Credenciais e-CNPJ/OAuth S2S, storage secrets, network, homologação | Security/Infra | `PENDING` |
| SRC-04 | Política LGPD/base legal, dados pessoais em QSA/contato, retenção, acesso, logs, DPA | Jurídico/DPO/Security | `PENDING` |
| SRC-05 | Mapeamento real externa → SA2/PUT, editabilidade e limits SX3 (conferir contrato no HEAD) | TOTVS/api-delpi + Suprimentos | `TO_INVENTORY` |
| SRC-06 | Escolha corporativa de owner adapter CNPJ (reuso fora de Suprimentos?) | Architecture | `TO_INVENTORY` |
| SRC-07 | Aceite de proposta do PO: on-demand, sem job automático, somente SA2 | PO | `PENDING` |
| SRC-08 | Freeze do contrato BFF, decisão persistente, TTL/retention e idempotência | Architecture + Security | `PENDING` |
| SRC-09 | Verificar disponibilidade dos dados abertos CNPJ e periodicidade oficial do dataset específico, se alternativa | Data/Engineering | `TO_INVENTORY` |
| SRC-10 | Homologação de testes de fonte real e check contra fornecedores de teste consentidos | QA/owner | `TEST_NOT_RUN` |

## 6. Evidence ledger

- `PROVEN` documentação oficial: Serpro disponibiliza serviço para PJ mediante contratação, uso e-CNPJ e consumer credentials; há custos ligados a tipo/volume de consulta. Conecta publica API CNPJ e schema, mas acesso descrito para órgãos públicos; REDESIM/Receita oferecem canal web de consulta; RFB publica iniciativas de dados abertos.
- `NOT PROVEN`: integração autorizada na DELPI, custo efetivo contratado, uso livre dos endpoints Conecta, API aberta da REDESIM, credenciais, qualidade/live response, dados atualizados de fornecedores reais, backend implementado.
- `PLANNED`: mapeamento e política de campos elegíveis; busca sob demanda; comparação e aceite/recusa; backend técnico proposto.
- `TARGET`: após gates, provider Serpro comercial ou alternativa oficialmente autorizada.
- `IMPLEMENTATION = NOT_AUTHORIZED`; `NO HTTP CALL TO CNPJ PROVIDERS`, `NO DB/MIGRATION`, `NO CODE CHANGE`, `NO DEPLOY`, `NO PROTHEUS PUT`.

**Próxima decisão:** avaliar contratação e acesso Serpro + validar schema da modalidade disponível, em paralelo com aprovação LGPD/retention e matriz SA2. Até lá, API/UX permanecem contrato proposto.
