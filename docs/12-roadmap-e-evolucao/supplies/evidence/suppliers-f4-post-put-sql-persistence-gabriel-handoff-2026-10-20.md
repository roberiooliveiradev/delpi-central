# Suppliers F4/F4.2 — Evidência de persistência REST↔SQL e handoff Gabriel
**Data:** 2026-10-20  
**Natureza:** consolidação de execução reportada pelo Cursor e verificada documentalmente; não substitui logs SQL/REST e aceite formal do owner.  
**Base consultada na redação:** `origin/main` SHA `16841cbd5f84b1643014775e75ad6e76852e277f`.  
**Decisão:** `ACCEPT` da descoberta F4.2; **GATE DE ESCRITA PRODUTIVA = BLOCKED**. Não habilitar flags sem contrato do ambiente produtivo e autorização de rollout.

## 1. Objetivo e situação real
Foi implementada a jornada `plugins/supplies → supplies-api → api-delpi → REST Protheus/Execauto MATA020`, com GET de listagem e ficha observados no Portal, formulário POST ampliado, PUT parcial de até 22 campos por decisão do PO, S2S individual via Keycloak, AuthZ funcional `supplies.access` no Core. Os detalhes runtime e field support devem ser conferidos no HEAD e nas evidências de testes específicas antes de nova alteração.

**Importante:** a listagem SQL atende a base produtiva `DELPI` enquanto a REST `:8701` comprovadamente corresponde aos dados em `DELPI_TST01`. Não divulgar como concluída a liberação operacional por essa divergência.

## 2. Inventário SQL read-only — relatório F4.2
Servidor SQL Server: `192.168.1.230`. Conexão SQL consultada via credencial autorizada `TOTVS_DB_*`; usuário REST `USR_PROTHEUS` não é conta SQL comprovada. Banco Intranet `IntranetDelpiDev` guarda `PARAMETROS_MINHADELPI`.

| Banco | SA2 ativos reportados | Max RECNO | 002469/01 | ZZ HOMOLOG F4 |
|---|---:|---:|---|---|
| `DELPI` | 3664 | 3714 | presente | ausente |
| `DELPI_TST01` | 3595 | 3645 | presente | **003878/01 presente** |
| `DELPI_TST_WS` | 3098 | 3147 | presente | ausente |

O registro `003878/01`, nome `ZZ HOMOLOG F4 FORNECEDOR TESTE`, está em `DELPI_TST01`, `SA2010`, `A2_FILIAL=''`, `A2_MSBLQL='2'` (bloqueado), `D_E_L_E_T_=' '` (não excluído). Identidade fiscal omitida neste documento. A chamada **GET REST pelo ID `00387801` retornou o mesmo fornecedor**, reportada como prova cruzada REST↔SQL. Ausência em `DELPI` e `DELPI_TST_WS` reforça isolamento. `DELPI_TST01` apresenta defasagem de registros em relação a `DELPI`.

**Classificação:** `PROVEN` pelo relatório de execução F4.2 (SELECT + GET REST coincidentes); associação formal de instância REST `:8701` ao DBAccess/ambiente TOTVS ainda `TO_INVENTORY` com Gabriel. Nenhuma nova escrita ocorreu em F4.2.

## 3. Resultados da homologação F4 — delimitação da prova
- **PUT REST:** nome fantasia, bairro, contato, indicador ROHS e condição de pagamento foram alterados em testes controlados e verificados por GET REST; PUT parcial e campos omitidos preservados nas amostras reportadas. Vários campos PUT permanecem sem homologação individual.
- **PUT upstream wire shape:** contrato original documentava `fornecedor: [ {...} ]`; teste real retornou 500 com array e aceitou `fornecedor: {...}`. Código/contrato atualizado em commit `1aabfb0851`. Registrar `EXECUTION_DRIFT` face ao documento externo original; pedir confirmação de Gabriel para homolog/produção.
- **POST REST:** depois da descoberta de obrigatoriedade de `phone` (`A2_TEL`), `financial_nature_code` (`A2_NATUREZ`) e `bacen_country_code` (`A2_CODPAIS`), retornou `200` com mensagem de inclusão. A evidência SQL F4.2 localizou o registro `003878/01` e o GET REST confirmou. O **POST não retornou `A2_COD`** no corpo; a reconciliação ocorreu posteriormente via SQL.
- **Identidade do ator:** execução reportada com login `rober`, `codusr=000311` resolvido via Core; verificação em `SYS_USR` foi reportada. Gabriel deve confirmar equivalência semântica e ambientes.
- **Regressões negativas:** `tax_id`, código e loja protegidos; `codusr` enviado pelo cliente precisa ser **rejeitado integralmente**, pois teste negativo com `codusr` em posição top-level na BFF foi descartado e outro campo válido chegou a gravar. Registro restaurado, mas **não repetir esse teste com fornecedor real**.
- **Gates:** CREATE/UPDATE foram temporariamente habilitados para a homologação F4 e, segundo relatório, desligados ao final: `PROTHEUS_SUPPLIER_CREATE_ENABLED=false`, `PROTHEUS_SUPPLIER_UPDATE_ENABLED=false`; conferir novamente no container antes de qualquer novo teste. Nenhuma autorização de go-live pode ser inferida do teste.
- **Segurança:** S2S individual Keycloak para `suppliers.read/create/update`, Core `supplies.access`; sem autorização de escrita SQL direta, nem retry automático de POST/PUT.

## 4. Divergências e resíduos classificados
| ID | Constatação | Estado / owner |
|---|---|---|
| F4-U01 | `REST :8701` corresponde a `DELPI_TST01`, lista SQL consulta `DELPI` | `PROVEN` em dados; mapa DBAccess formal `TO_INVENTORY` / Gabriel+infra TOTVS |
| F4-U02 | Endpoint REST de produção associado a `DELPI` não identificado | `BLOCKED` / Gabriel |
| F4-U03 | POST não fornece código+loja gerados; reconciliação precisa de mecanismo determinístico | `TO_INVENTORY` / Gabriel |
| F4-U04 | Campo obrigatório para POST: `phone`, `financial_nature_code`, `bacen_country_code` no ambiente testado | `PROVEN` via rejeições REST; harmonizar DTO/UI e confirmar variação por ambiente / api-delpi+TOTVS |
| F4-U05 | 20 campos PUT adicionais liberados no código por PO, sem homologação upstream campo a campo | `PENDING` / Gabriel+api-delpi |
| F4-U06 | `fornecedor` no PUT: documento externo array, execução REST objeto | `EXECUTION_DRIFT` / Gabriel |
| F4-U07 | `codusr` top-level do cliente descartado em vez de rejeitar request integral | `FAIL` de proteção contra efeitos colaterais / supplies-api |
| F4-U08 | Resposta upstream HTTP 400 pode se tornar 502 visível; classificar rejeição determinística sem confundir com indisponibilidade | `TO_INVENTORY` / api-delpi+supplies-api |
| F4-U09 | Cadastro de teste `003878/01` permanece bloqueado e não excluído em `DELPI_TST01` | `PROVEN`; owner TOTVS decide encerramento, sem DELETE SQL |
| F4-U10 | Credencial REST publicada em documento externo com segredo em texto claro, transporte HTTP relatado | `RISK`; owner infra/TOTVS confirmar rotação/mitigação |

## 5. Perguntas encaminhadas a Gabriel (owner REST Protheus)
1. Confirma que REST `:8701` usa DBAccess em `DELPI_TST01`? Qual empresa/ambiente Protheus?
2. Qual o endpoint REST que opera **sobre `DELPI` produtiva**, e como comprovar GET da mesma base, sem escrita?
3. Pode incluir `A2_COD` e `A2_LOJA` na resposta de sucesso POST, ou fornecer reconciliação segura por identificador?
4. Quais campos são obrigatórios no POST para cada tipo de fornecedor? No teste apareceram `A2_TEL`, `A2_NATUREZ`, `A2_CODPAIS`.
5. O PUT aceita objeto `fornecedor` em todos os ambientes? Quais dos campos cadastrais são realmente atualizáveis, inclusive edição múltipla? Regras de limpar/omitir?
6. Confirma `codusr` associado a `SYS_USR.USR_ID` e o tratamento em casos de timeout/ACK não persistido?
7. Qual a estratégia aprovada para o cadastro de teste `003878/01`?

**Handoff:** mensagem de e-mail enviada pelo usuário segundo a conversa; **entrega/resposta de Gabriel não verificada neste repositório**. Não inventar aprovação, prazo ou endpoint produtivo.

## 6. Próxima execução / gate
Aguardar contrato técnico do Gabriel e, em paralelo, corrigir a rejeição integral de identidade de cliente e validações obrigatórias POST com testes simulados. Após comprovar REST produtivo, comparar GET REST×SQL do mesmo ambiente e executar gate de rollout controlado aprovado pelo PO+TOTVS. **Não mudar `URL_REST` por inferência; não habilitar flags em produção; não gravar SA2 diretamente.**

## 7. Evidências e fontes
- Relatórios Cursor F3.3, F3.4, F4 e F4.2 apresentados nesta conversa: relatórios de execução, não artefatos brutos SQL.
- `api-delpi/docs/integrations/protheus-rest-supplier-api-contract.md` e `protheus-rest-supplier-write-handoff.md`.
- PDF externo `Documentação Técnica - API de Integração Protheus e MinhaDelpi (002)` (contém segredo: **não versionar**).
- Histórico de commits: `1aabfb0851` (PUT objeto), `1baf5059b2` (flags), `16841cbd5f` (documentação homologação).
