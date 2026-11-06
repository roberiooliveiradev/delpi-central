# DEVIN — IMPLEMENTAR AVATARES INLINE NOS MCPs DELPI

**TASK:** AVATAR-INLINE-MCP-V1  
**SOURCE OF TRUTH (ler integralmente):** `docs/12-roadmap-e-evolucao/correcao-mcps/PLANO-AVATAR-IMAGECONTENT-MCP-APPS-V1.md`  
**REPO:** `roberiooliveiradev/delpi-central`, branch `main`  
**OBJETIVO:** entregar a imagem original oficial do avatar no próprio ChatGPT quando o usuário perguntar sobre avatar/aparência, não apenas um link. Corrigir SURI no mesmo fluxo e preservar os demais.

## INSTRUÇÃO PRINCIPAL

Implemente exatamente o plano acima, sem criar outra arquitetura. **Não assuma que `ImageContent` será visualizado automaticamente na interface do ChatGPT; primeiro teste uma POC TÉO, depois compare com MCP Apps/UI e somente propague a opção que demonstrar imagem visível sem clique.** Se a UI ChatGPT não estiver disponível para teste, não declare aceite visual e descreva o procedimento manual e blockers.

DAVI encontra-se em refatoração: **NÃO ALTERAR NEM DEPLOYAR DAVI**. Apenas inventariar o impacto futuro de maneira não invasiva. Os seis serviços do rollout são TÉO, VISTA, CLARA, CAIO, SURI e EVA.

## ORDEM DE EXECUÇÃO

1. **Segurança do HEAD:** `git status`, `git rev-parse HEAD`, checar `origin/main`, arquivos dirty e trabalho paralelo, ler `AGENTS.md`, `.devin`/ `.cursor`, contrato `shared/delpi_character_profiles`, scripts canônicos de build/deploy e plano anexo. Não descartar alterações, não usar force push.
2. **Inventário e ownership:** localizar para cada owner seu `CharacterProfile`, asset, metadata `avatar_distribution`, rota pública, recursos MCP, SDK e adapters. Distinguir backend/API de serviço MCP, especialmente `delpi-supplies-mcp` versus `delpi-supplies-api`.
3. **POC TÉO:** medir GET público e SHA da foto oficial; implementar o mínimo read-only para retornar bytes reais em `ImageContent` e testar no cliente. Se não renderizar imagem inline, construir MCP Apps visual `ui://` com metadata corretamente vinculada à tool (conferir SDK instalado e especificação vigente), CSP restrita, HTML acessível, fallback textual e URL oficial. **Não criar imagem alternativa**.
4. **Gate de evidência:** comparar resultados e registrar a decisão de contrato. Não generalizar antes de prova visual; se ausência de acesso à UI impedir a prova, pode finalizar backend da POC com `PENDING` e entregar briefing de aceite, mas não fazer rollout indiscriminado.
5. **SURI obrigatória:** aproveitar foto existente e aprovada `avatar-preview-v1.png` e SHA, localizar rota equivalente ou implantar GET público allowlisted para avatar oficial, projetar metadata HTTPS owner-local `avatar_distribution` no catálogo sem quebrar contratos, integrar a ferramenta/componente escolhido; testar API e `supplies-mcp` nos ambientes e containers corretos. Sem inserir URLs arbitrárias ou arquivos em `shared`.
6. **Rollout:** VISTA, CLARA, CAIO, EVA; preservar avatares, nomes de arquivo, perfis e schema existente. CAIO tem metadata com `distribution`/`media_type`: respeitar compatibilidade; não padronizar destruindo consumidores.
7. **Testes por owner:** estado `OFFICIAL_AVATAR_APPROVED`, SHA, MIME, GET 200 sem token (apenas ativo público aprovado), HEAD/GET conforme implementação, 404 path inválido, segurança traversal, integração MCP ImageContent ou UI, fallback, texto de aparência fiel à ficha; nenhuma mutação de negócio. Rodar suíte relevante, residual search, `git diff --check`.
8. **Commit/push/deploy sequenciais:** um owner por vez, push seguro, identificar scripts reais, deploy MCP e API afetados, verificar SHA da instância verdadeira, reconsultar metadata, bytes de imagem e recursos; `health=200` sozinho não prova sucesso. Não criar commits artificiais quando código já estiver correto.
9. **Aceite no ChatGPT:** testar *"Mostre seu avatar"*, *"Como é sua aparência?"*, *"Mostre sua foto"* em cada MCP real, verificando foto **original** visível inline sem clique. "Quais suas ferramentas?" não deve inserir foto sem solicitação visual. Caso Devin não possa operar ChatGPT, fornecer uma matriz detalhada `TEST_NOT_RUN` e instruções de configuração/conexão ou passos de Builder necessários.
10. **Documentação:** atualizar plano, `ACEITE-AVATARES-MCP-2026-11-06.md`, README e relatórios por owner, com decisões, provas, screenshots/artefatos legítimos, status e pendências. Não apagar histórico de falhas.

## REGRAS NÃO NEGOCIÁVEIS

- **Shared owns structure. MCP owns character**: preservar `shared/delpi_character_profiles` e fichas locais; não criar registry central ou nova fonte de imagens.
- Avatar e visual são dados **narrativos públicos aprovados**, nunca autorização.
- Sem tokens/JWT/base64 em Knowledge, `agent_directives`, logs ou documentos; limitar recursos de imagem, validar MIME e não aceitar URL/path fornecido pelo usuário.
- Não confundir `ImageContent`, MCP Apps, ícone de GPT/plugin e imagem exibida na conversa.
- Sem alteração de OpenAPI/Actions/Knowledge por reflexo; só mudar quando contrato real pedir.
- **PROVEN** = fonte comprovada; **TARGET** = intenção futura; documentação e teste unitário não provam runtime.
- Para write de código/deploy, seguir gate de segurança, preservando trabalho paralelo; nenhuma gravação de negócio.

## POSTCONDITION E RELATÓRIO OBRIGATÓRIO

Para cada MCP emitir `TRANSFORMÔMETRO EXECUTION REPORT` com TASK, BASE HEAD, FINAL HEAD, STATUS, owner/source/contract, files, tests, OpenAPI/Actions, AuthZ, postcondition, authoritative read-back, residual search, gaps/risks, commit/push, deploy e ações manuais GPT Builder.

Produzir tabela consolidada:
`MCP | asset/ficha | URL HTTP | ImageContent/UI | renderização ChatGPT | tests | commit/push | deploy | runtime SHA | status`.

Se read-back ou visual não confirmar esperado: `OUTCOME_VERIFICATION_FAILED`. Se UI ChatGPT não puder ser testada: `TEST_NOT_RUN` para visual, mesmo que backend passe. Se cliente não suportar renderização inline neste canal, relatar limitação em vez de afirmar sucesso.

**EXECUTE A TASK AGORA, na menor sequência segura possível; não pare no planejamento.**
