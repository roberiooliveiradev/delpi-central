# Prompt para o Cursor — Home hub, H0 a H6

```text
PROMPT CURSOR — HOME HUB · H0 → H6 (Início do Portal Controladoria & Finanças no padrão do Comercial)

CONTEXTO
O Início do Portal Controladoria & Finanças tem os cards «Portal» (Início, Meu perfil) e «Central de
Fechamento» (fechamento, documentos, relatórios, Auditoria de Entradas e três itens de
administração). O owner decidiu alinhar ao padrão do Portal Comercial: tirar o card Portal, criar o
card «Notas fiscais» (Auditoria de Entradas + link do app Lançamento de Notas Fiscais), separar
«Administração» (só manage) e trazer os Favoritos como no Comercial (estrela em cada caminho,
«Favoritos» na barra do topo, persistidos na BFF).

FONTE DE VERDADE
docs/12-roadmap-e-evolucao/controllership-finance/home-hub/
  plan.md   ← hoje × alvo (§1), decisões D1–D8, favoritos (§3), ajuda, aceite (§5)
  track.md  ← etapas H0–H6, regras, paradas Z1–Z6, rollback, quadro e registro
Referência de código: plugins/commercial (pluginRouteCatalog.ts, hubRouteIcons.tsx, HomePage.tsx,
homeFavoritesApi.ts, homeFavoritesStore.ts, ShellFavoritesStrip.tsx e testes) e commercial-api
(V006__home_favorites.sql, home_favorites_routes.py, repositório e testes).
Autoridade: instruções oficiais do arquiteto e .cursor > padrão visual dos Portais >
30-plugin-ui-reuse-map.md > track.md > plan.md.

MISSÃO
Executar H0 → H6 sem parar entre etapas, documentando cada etapa no mesmo commit, publicando em HML
e depois em PROD. Parar SOMENTE numa parada Z1–Z6 ou ao concluir H6.

REGRAS INEGOCIÁVEIS
1. main, sem branch; git add só com caminhos explícitos (nunca -A, ., commit -a); push a cada etapa.
2. Sem permission nova. O link do LNF usa capabilities.lnfAccess (aditivo no /viewer-context),
   lido das permissões efetivas do Core com a mesma regra de entrada do app LNF.
3. Copiar o padrão do Comercial, não reinventar: mesmas peças, mesmo comportamento, componentes do
   @delpi/plugin-ui. Mudança no plugin-ui só aditiva e com prova dos consumidores.
4. Migration nova: V030. Nunca editar migration aplicada.
5. Aba nova na barra do topo só «Favoritos». Não criar aba de funcionalidade que não existe.
6. Sem dado real no repositório. Suítes comparadas ao commit pai; falha nova = Z2.
7. Página não aberta = INCONCLUSIVE, nunca PASS por inferência (remoteEntry 200 não basta).

REPORT (ao parar)
Formato do track: por etapa, o que mudou, SHA, testes, evidência. H0: tabela «peça do Comercial →
peça do CF» e o que o Comercial faz para D7/D8. H5: resultado do Playwright por perfil e
screenshots. H6: tags, imagens, Início aberto em PROD, favoritos persistindo. Quadro final.
```
