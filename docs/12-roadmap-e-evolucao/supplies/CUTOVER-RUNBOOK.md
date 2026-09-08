# CUTOVER-RUNBOOK — Portal Suprimentos

**Não executar nesta etapa.** Pré-requisitos: [HOMOLOGACAO-PARIDADE.md](./HOMOLOGACAO-PARIDADE.md) + [ADR-002](./adr/ADR-002-purchase-requests-api.md) + [ADR-003](./adr/ADR-003-legacy-app-consolidation.md).

Princípio: **target saudável primeiro; redirect por último**.

---

## 0. Gates obrigatórios

Antes de qualquer flip:

- [ ] E1 fechado ou cada pendência explicitamente bloqueada/aceita
- [ ] GATE-AUTHZ verde
- [ ] supplies-api saudável
- [ ] MFE supplies saudável
- [ ] Manifest validado/registrado
- [ ] permissions canônicas provisionadas no Core
- [ ] `/me/apps` e `/me/routes` validados com papéis reais
- [ ] aliases funcionando somente como compatibilidade
- [ ] C2 de Purchase Requests concluída + reconciliação
- [ ] paridade final assinada
- [ ] BIs externos sem `LEGADO_A_VALIDAR`
- [ ] rollback testado

---

## 1. Sequência operacional correta

```text
1. deploy supplies-api
2. health/ready OK
3. gateway conhece /apps/supplies-api sem redirect legado
4. deploy MFE supplies
5. remoteEntry/assets OK
6. registrar manifest supplies
7. provisionar RBAC canônico nos papéis/grupos
8. validar /me, /me/apps, /me/routes
9. smoke pela URL NOVA /apps/supplies
10. executar homologação final
11. somente agora ativar redirects legados
12. ocultar launcher legado gradualmente
13. observar telemetria
14. remover legado apenas com critérios comprovados
```

Nunca ativar redirect para target que ainda não passou smoke pela URL nova.

---

## 2. Redirects — somente após GO

Destinos precisam estar fechados antes do deploy. Não deixar “ou rota de foco” para o operador decidir no dia.

| De | Para alvo |
|---|---|
| `/apps/dashboard-supplies` | `/apps/supplies/overview` |
| `/apps/dashboard-supplies/cpv` | **BLOQUEADO até congelar rota/focus definitivo** |
| `/apps/dashboard-supplies/otd` | `/apps/supplies/suppliers/otd` |
| `/apps/dashboard-supplies/stock` | `/apps/supplies/inventory` |
| `/apps/dashboard-supplies/inventory-turnover` | **BLOQUEADO até congelar representação do giro** |
| `/apps/dashboard-supplies/negotiation-savings` | `/apps/supplies/negotiations` |
| `/apps/purchase-requests` | `/apps/supplies/purchase-requests` |
| `/apps/estoque-seguranca` | `/apps/supplies/safety-stock` |
| `/apps/estoque-seguranca/analise-consumo` | `/apps/supplies/safety-stock/consumption-analysis` |

Qualquer linha `BLOQUEADO` precisa ser resolvida antes do `GATE-CUTOVER`.

BIs externos só recebem redirect/deep link após E1.S1 revelar id/path real e a decisão final ser homologada.

---

## 3. RBAC de coexistência

Aliases no BFF preservam compatibilidade de autorização interna, mas não tornam o novo app visível automaticamente.

Antes do GO:

1. registrar permissions canônicas do `supplies`;
2. adicionar `supplies.portal.access` e capabilities necessárias aos papéis/grupos equivalentes;
3. adicionar unit permissions canônicas;
4. manter permissions legadas durante a janela de coexistência;
5. validar usuários positivos/negativos em `/me/apps` e `/me/routes`.

Não remover permissions antigas no mesmo momento do primeiro flip.

---

## 4. Purchase Requests C2 antes de C3

C3 é o cutover/desligamento da `purchase-requests-api`. Portanto:

```text
C1 gateway
→ paridade inicial
→ C2 ownership do schema/jobs
→ dual-read/reconciliação
→ freeze legado
→ paridade final
→ C3 redirect + desligamento
```

É proibido executar o redirect final de Purchase Requests enquanto `purchase-requests-api` ainda for dona exclusiva de jobs/estado necessário ao funcionamento do fluxo alvo.

---

## 5. Deploy seguro

Usar scripts sequenciais canônicos conforme ambiente. Exemplo conceitual, ajustar aos flags reais no momento da execução:

```bash
./infra/scripts/up-prod-sequential.sh --pull --build supplies-api
./infra/scripts/up-prod-sequential.sh --fase mfe --build supplies
# gateway somente quando a config do target estiver pronta; redirect legado é passo posterior e separado
```

Não usar `docker compose up --build` em lote.

---

## 6. Smoke antes de redirect

Validar pela URL nova:

- Home;
- Overview;
- SC;
- pedidos/entregas;
- estoque/ESTSEG;
- Produto 360;
- Fornecedor 360;
- Ajuda;
- 403 por unidade;
- usuário sem app;
- `/me/apps`/`/me/routes`;
- partial failure dos BFFs compostos.

---

## 7. Rollback

Rollback deve ser praticável sem remover o Portal novo:

1. desativar snippet de redirects;
2. reexpor launcher legado se ocultado;
3. manter permissions/aliases antigos durante a janela;
4. supplies pode permanecer disponível para investigação;
5. não reverter migrations de forma destrutiva.

Se uma migration/config nova impedir a versão anterior de subir, o runbook deve preferir roll-forward ou expand-and-contract e registrar isso antes do GO.

---

## 8. Janela de segurança e remoção

Não usar apenas “2–4 semanas” como critério.

Para cada legado registrar:

| Campo | Obrigatório |
|---|---|
| owner | sim |
| replacement | sim |
| startDate | sim |
| knownConsumers | sim |
| telemetry | sim |
| removalCriteria | sim |
| rollback | sim |

Critérios mínimos sugeridos para remoção, a homologar:

- paridade assinada;
- zero dependências conhecidas não migradas;
- uso das URLs antigas abaixo do threshold acordado por janela definida;
- favoritos/deep links migrados ou redirecionados;
- RBAC canônico estabilizado;
- rollback testado;
- ADR-003 atualizado para executado.

Se a janela temporal ainda depender do PO, marcar `NECESSITA_VALIDACAO_FUNCIONAL`; os critérios técnicos permanecem obrigatórios.
