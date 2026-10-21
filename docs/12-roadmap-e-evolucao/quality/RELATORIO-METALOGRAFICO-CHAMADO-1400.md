# Relatório Metalográfico de Crimpagem — especificação de evolução

> **Chamado de origem:** Helpdesk #1400 — “Relatório Metalográfico”, aberto em 21/10/2026 por José Carlos de Lima Junior.  
> **Status:** PLANNED — especificação documental; implementação, testes e deploy NÃO realizados.  
> **Artefato analisado:** `Modelo_Relatorio_Metalografico_Delpi_Editavel (6).html`, HTML fornecido pelo solicitante no atendimento.  
> **Integridade do arquivo recebido:** SHA-256 `13ba5eb7033afa616bf542ac6f7a6df5c67a0d318d2ea898caa4fb368220b820`. O HTML original **não foi incorporado ao repositório** nesta entrega; deve ser preservado como anexo do chamado e disponibilizado ao executor por canal autorizado. Não embutir fontes/imagens/base64 massivos em documentação.  
> **Natureza:** backlog e requirements, NÃO contrato aprovado nem evidência de runtime.

## 1. Necessidade e resultado esperado

Integrar ao Minha DELPI uma experiência para produzir, editar, consultar e exportar relatórios de análise metalográfica de crimpagem de terminais. Reutilizar o modelo de documento recebido como referência visual/funcional, adaptando a interface interativa ao design system da plataforma **sem alterar o formato técnico do relatório em PDF**. Persistir relatórios e seus anexos no armazenamento servidor autorizado, não exclusivamente no browser. O solicitante também pede verificar o local correto de salvamento no banco do servidor: **a definição física e o owner do datastore permanecem TO_INVENTORY** até inspeção do domínio.

### Baseline comprovada no HTML recebido (não no portal)

A aplicação standalone possui uma tela inicial com listagem de relatórios salvos, filtros combinados por data e identificação da amostra, criação de novos relatórios e editor A4. O editor permite salvar, exportar PDF e imprimir; oferece retorno com confirmação de dados não salvos, copiar relatório, excluir com confirmação, carregar duas imagens e recortá-las/centralizá-las. Há código de persistência IndexedDB e fallback localStorage, inclusive numeração local. Isto **não prova** persistência central, autenticação, autorização, numeração única no servidor ou integração federada.

## 2. Escopo da página

### 2.1 Lista / acervo

- Cabeçalho com título, descrição e ação **Novo Relatório**.
- Listagem com identificadores, data, resultado e ações existentes (conferir detalhes/representação no HTML).
- Filtros aplicados em conjunto: data inicial/final; terminal; part number do terminal; produto/chicote; cabo; seção do condutor; aplicador/ferramenta; prensa/equipamento; lote/ordem de produção; amostra.
- Regra do protótipo: se a data do relatório estiver vazia, o filtro de período considera a data de criação. Validar semântica final junto ao owner antes de tornar contrato.
- Estados: carregando, nenhum relatório, nenhum resultado de filtro, erro recuperável, acesso negado.

### 2.2 Editor / relatório A4

**Metadados:** número do relatório, data, revisão.

**01 — Identificação da amostra:** terminal (código DELPI); part number do terminal; produto ou chicote (código/revisão); cabo (código DELPI/descrição); seção do condutor (mm²/AWG); aplicador/ferramenta; prensa/equipamento; lote/ordem de produção; amostra analisada.

**02 — Análise da seção transversal:** micrografia original (imagem óptica sem marcações) e imagem da seção com medições (áreas e cotas). Para cada imagem, upload e ferramenta de recorte/centralização com prévia e confirmação; manter proporcionalidade e sem distorção no documento.

**03 — Resultados da medição:** cada parâmetro possui `critério / tolerância` e `valor medido`:
- altura de crimpagem (CH) [mm];
- largura de crimpagem (CB) [mm];
- porcentagem de vazios (AV) [%];
- altura da rebarba esquerda (GH-E) [mm];
- altura da rebarba direita (GH-D) [mm].
Inclui esquema de referência das cotas. **Não inventar limites de engenharia** nem inferir conformidade automaticamente sem critérios oficiais do domínio.

**04 — Conclusão técnica:** resultado geral Conforme/Não conforme e observações/desvios.

**05 — Responsável pela análise:** nome do analista, com possibilidade de vinculação à identidade institucional após validação de regra de negócio.

**Rodapé/documento:** “DELPI | RELATÓRIO DE ANÁLISE METALOGRÁFICA”; ressalva de que os resultados se referem às amostras descritas; paginação. Respeitar a composição técnica do PDF de referência.

### 2.3 Ações e preservação do comportamento

Criar novo; salvar; reabrir e atualizar; duplicar com novo identificador; excluir com confirmação e autorização; voltar com aviso de mudanças não salvas; filtrar/limpar; recortar/restaurar imagem; exportar PDF; imprimir. Salvar e emitir são operações distintas. Não afirmar sucesso de gravação até confirmação do servidor.

## 3. Arquitetura e boundaries — decisão pendente de inventário

- **Host e navegação:** Portal Minha DELPI, segundo seus contratos de registro de app/rota.
- **UX compartilhada:** reutilizar `@delpi/plugin-ui` e tokens oficiais; CSS escopado à aplicação; responsividade, temas e acessibilidade.
- **Owner funcional provável:** frente de Engenharia/Qualidade, **a confirmar** pelas authorities e consumidores do HEAD. Não presumir que a API DELPI, Core ou Portal seja dona dos registros metalográficos.
- **Identidade / permissão:** Keycloak/AuthN e autorização central e de domínio segundo contratos efetivos; não confiar em botão oculto ou em claims isoladas.
- **Dados e imagens:** serviço e armazenamento do owner de domínio a descobrir. Core não deve se tornar banco de registros metalográficos por conveniência.
- **PDF:** versão final preserva seções, unidades, disposição técnica, imagens e legibilidade; abordagem de geração e retenção a decidir por owner/contrato.
- **Integração:** rota, manifesto, BFF/API, schema, permission codes e migração devem ser descobertos e definidos antes do código; não criar endpoint especulativo.

`EXISTING_EQUIVALENT = TO_INVENTORY` para plugin, API e repositório de relatórios; `REUSE_DECISION = PENDING` até busca em authorities, implementação e consumers. Para a UI compartilhada, **prioridade REUSE/EXTEND** após inspeção de exports reais.

## 4. Requisitos verificáveis

| ID local deste briefing (substituir por IDs canônicos existentes, se encontrados) | Requisito | Critério de aceite |
|---|---|---|
| RQ-01 | Aplicação acessível pela navegação autorizada do Minha DELPI | AC-01: app abre federado com acesso permitido; acesso negado é bloqueado no backend |
| RQ-02 | Formulário preserva os campos, seções e unidades do HTML | AC-02: round-trip dos campos sem perda |
| RQ-03 | Upload de micrografia e seção medida com recorte | AC-03: imagens persistem, reabrem e aparecem sem distorção no PDF |
| RQ-04 | Salvar, editar e consultar registros no servidor | AC-04: registro aparece ao entrar em outro navegador/sessão com o mesmo usuário autorizado |
| RQ-05 | Listar e filtrar relatórios | AC-05: filtros combinados e estados vazio/erro/negado funcionam |
| RQ-06 | Copiar e excluir com segurança | AC-06: cópia não altera original; exclusão requer autorização e confirmação; concorrência tratada |
| RQ-07 | PDF técnico idêntico em conteúdo e estrutura relevante à referência | AC-07: checklist comparativo em A4 valida seções, unidades, ordem, imagens, paginação e dados preenchidos |
| RQ-08 | Visual integrado ao ecossistema | AC-08: kit compartilhado, temas, desktop/mobile, teclado e foco; sem vazamento CSS |
| RQ-09 | Rastreamento e integridade | AC-09: autoria, datas, revisão, IDs únicos e histórico/auditoria aplicável conforme política do owner |
| RQ-10 | Separação entre edição e emissão | AC-10: exportação não altera silenciosamente o registro e falha de salvamento não é exibida como sucesso |

## 5. Contrato candidato — NÃO APROVADO

Antes de implementar, formalizar com owner e consumidores: identidade do relatório; esquema e tipos de cada campo; versionamento/revisões; anexos de imagem (formato, limites, integridade, antivírus/validação); política de numeração **server-side** e concorrência; listagem/paginação/filtros; CRUD autorizado; cópia; exportação; erros (validação, 401/403, 404, 409, 413, 422, 5xx); idempotência e ETag/controle de concorrência se aplicável; storage de arquivos e banco; retenção/backup; auditoria e observabilidade; compatibilidade; rollback. Adotar OpenAPI e operationIds estáveis quando aprovado.

**Dados antigos no navegador:** avaliar importação/migração apenas se houver necessidade, consentimento, política e estratégia de deduplicação aprovados. Não fazer upload implícito de conteúdo local.

## 6. Regras visuais e de documento

A interface pode adotar cabeçalho, cards, inputs, dialogs, toasts, tipografia, tokens, ações e navegação nativos do Minha DELPI. Entretanto o **documento PDF é um artefato técnico separado** e não deve mudar sua semântica/diagramação arbitrariamente. Validar impressão A4, margens, fontes autorizadas, escala das micrografias, contraste, quebra de página, campos extensos, paginação e resultados Conforme/Não conforme. Fontes embedded no HTML recebido devem ser inventariadas quanto à licença e uso; não distribuir fonte extraída sem verificação.

## 7. Segurança e privacidade

AuthN/SSO institucional, AuthZ live no backend, menor privilégio; diferenciar criar, ver, editar, excluir, exportar e administrar; validação de arquivos e conteúdo, tipos MIME e limites; sanitização de texto de observações; prevenção de XSS, upload indevido, enumeração de IDs e IDOR; URL assinada/stream autorizado quando necessário; logs sem dados pessoais desnecessários; backups e retenção do owner. Acesso a arquivos armazenados deve passar por permissão, não por URL pública presumida.

## 8. Plano bounded proposto (não execução)

1. **Reancorar** branch/HEAD remoto, instruções, .cursor, ADRs, owners, APIs existentes, manifestos, plugin-ui, roadmap e ledger; confirmar se já há solução equivalente.
2. **Inventário do HTML** funcional, comparação por seções, fluxo e PDF de referência; capturar screenshots/artefatos válidos com autorização e preservar o arquivo original fora de commit sem controle.
3. **Congelar contrato e ownership** com Engenharia/Qualidade, Core/Portal e API proprietária; decidir storage, permissão, numeração e política de versão.
4. **Implementar menor diff** de persistência e endpoints aprovados, depois UI e navegação, depois PDF, sempre reutilizando componentes existentes.
5. **Validar** round-trip entre navegadores, ACL negativa/IDOR, uploads, concorrência, filtros, cópia, exclusão, exportação A4, temas/mobile/a11y, builds e smoke federado.
6. **Entregar** diff, testes/CI, evidência vinculada ao SHA, PR/review/merge governado, eventual deploy aprovado e resultado observado no Portal.

**STOP:** owner de dados ou segurança sem definição; necessidade de mudar PDF técnico sem aceite da área; equivalente existente não inventariado; contrato não aprovado; qualquer breaking change sem plano de migração.

## 9. Evidências e estado nesta entrada

- **PROVEN (arquivo fornecido):** campos, seções, ações e persistência em navegador implementadas no HTML de referência; a origem e o hash foram registrados.
- **PROVEN (repositório consultado):** documentação geral situa iniciativas novas em `docs/12-roadmap-e-evolucao/`; regra `platform-frontend-mfe-experience.mdc` indica prioridade de `@delpi/plugin-ui`, responsabilidades e gates de UX.
- **TO_INVENTORY:** owner real do app/domínio, equivalente já existente, API/DB/objeto de armazenamento, autorização final, numeração, estratégia PDF, rota MFE, plano de implantação e requisitos industriais formais.
- **TEST_NOT_RUN:** não houve build/teste do HTML no navegador, validação PDF, teste de integração ou teste de produção.
- **PENDING:** implementação, contrato aprovado, PR de código, merge de software e deploy.

Este documento não declara o chamado resolvido; ele registra o requisito para execução subsequente.
