# Portal de Engenharia — homologação e paridade

> **Status:** contrato de validação para rollout.  
> **Objetivo:** impedir cutover baseado apenas em build verde ou percepção visual.

## 1. Princípio

Paridade é comprovada por comportamento, dados, permissions e deep links para a mesma persona/recorte. Diferença intencional precisa de decisão documentada e aceite do Product Owner.

## 2. Gates

```text
GATE-ARCH
GATE-AUTHZ
GATE-RBAC
GATE-API
GATE-MFE
GATE-FEATURE por página
GATE-PARITY por legado
GATE-CUTOVER
VERIFY-FINAL
```

Nenhum gate vira PASS por inferência. Evidência indisponível = `INCONCLUSIVE`.

## 3. Personas mínimas

Preparar usuários reais/testáveis para:

1. usuário com apenas acesso base ao Portal;
2. usuário com analytics;
3. usuário com LMP leitura;
4. usuário com escrita de NC;
5. usuário com Produtos/Documentos;
6. usuário com custo/preço sensível, se permission existir;
7. usuário sem a permission alvo;
8. usuário removido/não-membro de sala para teste IDOR;
9. perfil gestor/admin somente quando capability real existir.

Superadmin não substitui persona negativa.

## 4. Paridade — dashboard-engineering → Visão geral

Mesmo período/fonte:

| Item | Legado | Portal | Aceite |
|---|---|---|---|
| projetos no prazo | medir | medir | sem divergência não explicada |
| meta | medir | medir | mesmo owner SI |
| score/IDD | medir | medir | mesmo valor/arredondamento canônico |
| TRANSFORMA+ realizado | medir | medir | mesma fonte |
| TRANSFORMA+ meta/score | medir | medir | mesma fonte SI |
| loading/erro | registrar | registrar | Portal igual ou melhor, sem mascarar falha |
| permissions | mapear | mapear | nenhuma ampliação indevida |
| deep links | mapear | mapear | destinos equivalentes/redirect definidos |

A UI pode ser diferente; a semântica não pode mudar silenciosamente.

## 5. Paridade — dashboard-lmps → LMPs

Inventariar e marcar `PASS/FAIL/N/A`:

- resumo/KPIs;
- filtros;
- pesquisa;
- lista;
- paginação/ordenação;
- detalhe LMP/OV;
- produtos da LMP;
- estrutura/BOM quando presente;
- histórico de eventos;
- fluxo/lead;
- Gantt;
- listagem de NC;
- criação de NC;
- edição de NC;
- exclusão de NC;
- permissions `view`/`nc.write`;
- export/download se o legado realmente possuir;
- estados loading/empty/error;
- deep links;
- F5/back-forward.

Qualquer feature do legado não absorvida precisa de decisão: `MANTER_LEGADO`, `DEEP_LINK`, `FORA_DO_ESCOPO_COM_ACEITE` ou `PARIDADE_FUTURA`.

## 6. Sala de interação

Não existe legado Engenharia equivalente; validar contra contrato P0 e padrões de maturidade do Comercial sem exigir identidade de implementação.

### Dois browsers

```text
A e B autorizados na mesma sala
A envia → B recebe sem F5
B reage → A recebe
A menciona B → B recebe evento/notificação conforme policy
A edita/exclui → B converge
A abre sala X; B está em Y → evento X não vaza para Y
```

### Negativos

- UUID inválido;
- sala inexistente;
- usuário não-membro;
- usuário sem `engineering.access`;
- Core indisponível durante authorization;
- arquivo não autorizado;
- reconnect sem duplicação.

## 7. Minhas tarefas

Validar por owner:

- item LMP;
- item Controle MP quando integração existir;
- item NC se owner fornecer;
- source indisponível;
- source proibido;
- deep link;
- actions vazias quando owner não fornece;
- nenhuma ação inventada no MFE;
- filtros URL/F5/back-forward.

## 8. Produtos

Comparar diretamente com contratos api-delpi para amostra representativa:

- busca por código;
- descrição/part number quando suportado;
- detalhe;
- structure/BOM;
- parents/where-used;
- drawing;
- stock;
- suppliers;
- price/cost com permission apropriada;
- produto inexistente;
- dado parcial.

## 9. FILESERVER/documentos

Teste de segurança obrigatório:

- documento dentro da biblioteca allowlisted;
- documento inexistente;
- `document_id` manipulado;
- tentativa de `../`/path traversal;
- raiz não autorizada;
- extensão bloqueada;
- arquivo acima do limite;
- share indisponível;
- usuário sem permission;
- resposta nunca expõe path físico/credencial.

## 10. TopBar e shell

Testar presença **e ordem**.

Com todas as capabilities principais:

```text
Início
Visão geral
Sala de interação
Minhas tarefas
LMPs
Ajuda
```

Com capability condicional ausente, o item correspondente pode ser omitido, mas a ordem relativa dos demais permanece.

Também validar:

- Ctrl+K;
- Favoritos;
- launcher Ferramentas;
- perfil/avatar;
- hamburger/overflow;
- mobile;
- light/dark;
- keyboard.

## 11. Smoke federado

Executar no Portal real, não somente standalone:

1. login OAuth/OIDC;
2. app aparece pelo Core;
3. remoteEntry 200;
4. mount;
5. navegação interna;
6. F5 em rota filha;
7. back/forward;
8. 403/404;
9. console sem erro relevante;
10. unmount/remount sem listener/socket duplicado.

## 12. Evidência quantitativa

Salvar, quando material:

- payloads sanitizados;
- IDs/períodos usados;
- screenshots de comparação visual quando útil;
- tabela legado×target;
- resultados de testes;
- hash/versão do commit;
- persona/permission sem dados pessoais desnecessários.

## 13. Matriz de resultado

| Requisito | Teste | Resultado | Evidência | Bloqueia GO? |
|---|---|---|---|---|
| RQ-* | comando/smoke | PASS/FAIL/INCONCLUSIVE | arquivo/log | sim/não |

`INCONCLUSIVE` em AuthZ, persistence, realtime, paridade ou deep link crítico bloqueia cutover.

## 14. Critérios de aceite do GATE-PARITY

- dados críticos equivalentes;
- permissions sem ampliação;
- ações do legado preservadas ou decisão explícita;
- deep links/redirects definidos;
- sem regressão de F5/back-forward;
- Help atualizado;
- mobile/light/dark/keyboard aprovados;
- rollback conhecido;
- Product Owner aceita divergências intencionais registradas.

## 15. Verify-final

Após todas as ondas P0:

- reconstruir o pedido original;
- conferir cada `RQ-*`;
- rodar gates finais;
- verificar que o usuário encontra trabalho, indicadores, colaboração, LMPs e ferramentas no Portal;
- confirmar que nenhum owner foi duplicado;
- confirmar que legados só foram removidos após paridade;
- registrar pendências P1/P2 separadamente.
