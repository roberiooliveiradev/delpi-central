# Portal PCP: origem inicial da Demanda por filial (#1554)

## Necessidade
A aba **Demandas** deve iniciar em **Todas** (Protheus + MyWEG) na
filial 02, e em **Protheus** na filial 01. A escolha manual do usuário deve
continuar durante buscas, paginação, atualizações e filtros dentro da filial.

## Diagnóstico
A implementação anterior já usava "both" na montagem inicial do estado
quando aberta diretamente na filial 02. Porém, no `useEffect([branch])`
o valor `current.origin || "both"` mantinha a preferência Protheus ao
trocar da filial 01 para 02, em vez de adotar o padrão da nova unidade.

## Solução
- `utils/demandOrigin.ts` centraliza a regra
  `defaultDemandOrigin(branch, canViewMyweg)`.
- Filial **02** com permissão `production-control.myweg-needs.view`
  ou superadmin: início em `both` (rótulo **Todas**).
- Filial **01** ou filial 02 sem acesso MyWEG: início em `protheus`.
- `App.tsx` usa `key={activeBranch}` em `DemandPage`, para recriar
  filtros de forma independente a cada troca de filial. Não depende de
  timing de um efeito de correção que dispare consulta com origem velha.
- `DemandPage` recebe permissões da sessão e oculta o filtro de origem
  MyWEG quando indisponível; a API continua validando RBAC.
- Em eventual revogação da permissão durante a sessão, a tela retorna
  para `protheus`, removendo uma origem restrita.
- Busca, ordenação, paginação, filtros de clientes e botão Atualizar não
  alteram uma escolha manual de origem. O botão Limpar redefine ao padrão
  **da filial ativa**.

## Escopo e segurança
Só o frontend do plugin `production-control` mudou. O cálculo da
cobertura e as regras de consolidação MyWEG e Protheus permanecem os
mesmos no BFF. Não há escrita em Protheus, em snapshots MyWEG nem
migração de dados.

## Critérios de aceite
1. Entrar direto na filial 02 autorizado: origem `both`.
2. Trocar da filial 01 (Protheus) para a 02: origem `both`.
3. Entrar na 01, inclusive superadmin: origem `protheus`.
4. Filial 02 sem permissão MyWEG: somente Protheus e sem opções MyWEG.
5. Filial 02 autorizada: escolher Protheus manualmente e paginar /
   atualizar, sem retornar indevidamente a Todas.
6. Superadmin na filial 02: origem `both`.
7. Typecheck, testes frontend e build do Portal PCP aprovados.

Deploy: reconstruir somente `production-control`.
Após publicar, validar os cenários acima no navegador e confirmar com
o solicitante antes de encerrar o chamado #1554.
