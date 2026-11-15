# Prompt para o Cursor — UI review, U9 (rework da revisão U0–U8)

```text
PROMPT CURSOR — UI REVIEW · U9 — fechar o que a U7/U8 deixou INCONCLUSIVE

CONTEXTO
Revisão do Claude sobre U0–U8 (15/11/2026): o redesenho está aceito; o kit (title opcional no
SectionRouteCard) é aditivo e testado; ClosingHero usa CfPageHero (conforme §10). Ficaram quatro
pontos. Detalhe em ui-review/track.md §7.

R1 · Alta · Abertura da análise ≈ 9,0 s (01/11–15/11, 315 notas)
   O review G9 pediu: carregar resumo + breakdowns primeiro e as abas sob demanda, paginação no
   servidor. O U0 registra que a página ainda carrega «summary + breakdowns + rows no mount» e não
   há medição antes/depois.
   Fazer: medir por requisição (summary, breakdowns, daily, occurrences, documents…) com tempos;
   mostrar hero + KPIs assim que o summary chega; gráficos quando os breakdowns chegam; aba ativa
   só quando aberta, paginada no servidor. Se o gargalo for a BFF (consulta), otimizar a consulta
   (índice/agregação) sem mudar contrato. Meta: KPIs visíveis < 1,5 s e página utilizável < 3 s
   na mesma análise. Reportar antes/depois por requisição.

R2 · Alta · Usuários de teste por perfil no HML — terceira trilha sem eles (H5, U7)
   A regra 9 da trilha da auditoria autoriza e o Cursor já criou clientes e escopos no Keycloak de
   HML na T6. Criar agora: cf-access (só access), cf-manage (access+manage), cf-lnf (access + uma
   permissão do LNF), cf-dre (accessDre), senha só no .env.hml, registrados no provisionador de HML.
   Se faltar algo para criar (credencial de admin, realm, script), PARAR e dizer exatamente o que
   falta — não marcar INCONCLUSIVE sem motivo.
   Depois: Playwright por perfil no Início (cards certos), na Auditoria e na Administração (403 sem
   manage).

R3 · Média · Acessibilidade e temas sem prova
   Adicionar @axe-core/playwright como devDependency do MFE e rodar nas páginas mexidas (Início,
   entrada, resultado com cada aba, detalhe): sem violação serious/critical nova. Playwright com
   colorScheme light e dark nas mesmas páginas (screenshots no report, não commitados).

R4 · Média · Página do usuário do Portal (§7 do padrão é obrigatório, não V5)
   O avatar leva ao /profile do Core. O padrão exige /apps/controllership-finance/users/{userId}
   com PortalUserProfilePage, como no Comercial e em Suprimentos
   (plugins/commercial/src/features/users/UserProfilePage.tsx). Implementar no mesmo padrão, com o
   avatar da TopBar abrindo essa página. Se o conteúdo exigir dado que a BFF não entrega, V4.

REGRAS
As da trilha U0–U8 (main sem branch; git add só com caminhos explícitos; Cf* do kit; sem mudança de
regra/contrato/permissão; HML antes de PROD; tag rollback-ui-review-u9-<artefato>).
PROD: publicar e, como não há usuário de teste em PROD, parar e pedir ao owner os prints do Início,
da entrada e da análise 01/11–15/11 no celular e no desktop (o owner verifica).

REPORT
R1 com tempos antes/depois por requisição; R2 com os usuários criados (sem senha) e o resultado por
perfil, ou o bloqueio exato; R3 com o resumo do axe e screenshots claro/escuro; R4 com a rota e o
teste. Atualizar track.md. Parar ao concluir.
```
