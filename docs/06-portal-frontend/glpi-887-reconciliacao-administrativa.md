# GLPI #887 - Painel administrativo de reconciliação de identidades RH

## Contexto real (18/11/2026)

Na equipe do gestor matrícula `20001`, a hierarquia RH retornou 63 ativos.
A Core API apurou **0 vínculos Core verificados**. A prévia de reconciliação
apresentou **8 sugestões por nome**, **55 sem sugestão por nome**, sem
duplicidade detectada nesta amostra.

Um resultado `no_exact_name_suggestion` não significa que a pessoa não
possui usuário da Minha Delpi. Não há comprovação de que os 8 resultados
correspondam aos 9 candidatos detectados no cadastro local do Portal RH.
**Nenhum dos 63 vínculos foi criado automaticamente.**

## Escopo da PR

- Nova aba `Administração > Identidades RH` no portal.
- Entrada de matrícula do gestor e opção de equipe direta/indireta.
- Usa o endpoint já existente `GET
  /admin/organization/managers/{registration}/identity-review?details=true`.
- Exibe contagem, filtro de situação e linha por colaborador para TI/RH com
  `rbac.manage` **e** `users.manage` (API faz a checagem).
- Sugestão por nome continua sendo uma **pista fraca**, nunca uma identidade
  confirmada. O operador deve abrir o cadastro do usuário e validar dados em
  fonte oficial; não cadastrar apenas porque o nome coincide.
- Para colaboradores sem sugestão, permite busca manual nas contas da Core
  sem assumir que não existe conta.
- Somente uma associação por vez: selecionar UUID Core, declarar conferência
  humana de identidade, digitar matrícula exata, informar referência de
  evidência (ex.: ticket GLPI, documento RH), revisar modal final e confirmar.
- Verifica se a conta Core já tem matrícula diferente antes de enviar;
  reusa o `PUT /admin/organization/users/{user_id}/hr-registration`
  já protegido com `confirmIdentity=true`. O backend também impede
  matrícula atribuída a outra conta e rejeita usuários inativos.
- Após confirmar, consulta a equipe novamente para refletir o vínculo.
- Sem ação em lote, importação CSV, heurística de autoaprovação, nova
  migração, criação de identidade Keycloak ou acesso por supervisores.

## Auditoria

O backend aceita um campo opcional `verificationReference` de 5 a 120
caracteres sem controles, gravado no payload da auditoria
`hr_registration.verified_upsert`, junto com matrícula anterior/nova,
administrador autenticado e endereço IP. Campo é opcional para
retrocompatibilidade com integrações administrativas já existentes;
o novo painel o exige para criar associações.

A referência deve identificar onde a conferência foi feita, sem
incluir senha, CPF completo, documentos pessoais ou outros dados
sensíveis em texto livre.

## Pontos de atenção

1. O painel lista nomes e matrículas **somente após ação do administrador**,
   sem download/exportação ou persistência local desses dados.
2. 8 sugestões por nome = **0 identidades comprovadas**. Conferência humana
   deve comparar o RH oficial e a conta de login (Keycloak/Core) sem
   assumir que `users.id` sempre equivale ao `sub` do Keycloak.
3. Nenhuma mudança no Portal RH: preserva o grande conjunto de alterações
   locais de produção desenvolvidas pelo Cursor.
4. A apuração semanal ainda não pode produzir estatísticas por equipe
   enquanto `user_hr_registrations` estiver sem vínculo aprovado.
5. Relatório nominal de acesso a supervisores e agendamento Delpi Reports
   são etapas futuras com autorização por gestor e avaliação LGPD.

## Guia de uso da interface

Acesse `/admin?tab=identity`, informe `20001`, clique **Consultar equipe**,
filtre por **Sugestão por nome**, selecione um colaborador, abra o cadastro da
conta sugerida ou pesquise outra conta Core, confirme a fonte oficial,
preencha a referência da evidência e digite a matrícula para aprovação
individual. Se houver divergência, **cancele**, não associe.

## Smoke após merge e publicação

- Usuário sem permissão: API de detalhes e PUT retornam 403.
- Admin com as duas permissões: GET mostra 63 membros (se a hierarquia for
  idêntica); 8 sugestões / 55 sem sugestão, antes de novas associações.
- Validação da referência rejeita quebra de linha e texto muito longo.
- Nenhuma mudança no banco ao abrir ou consultar o painel.
- Um único vínculo **confirmado humanamente** passa a aparecer como
  `verified_mapping` após a atualização e como mapeado na apuração semanal.
- Não acionar envio automático de e-mails nem liberar a gestores.

## Testes de código

```bash
cd core-api
pytest app/tests/test_portal_rh_organization.py app/tests/test_glpi_887_identity_review.py -q
```

O frontend segue o pipeline `portal/package.json` com
`npm run build` em um checkout de desenvolvimento. Não executar testes
no diretório de produção para evitar interferência em builds em uso.

## Publicação

Após o usuário decidir o merge, atualizar **somente** o monorepo
`delpi-central`, sem tocar no Portal RH e sem executar `reset --hard` ou
`clean`. Como a PR altera Portal e Core API, avaliar a janela operacional
antes de reconstruir os serviços `core-api` e `portal` individualmente.
A inicialização da Core pode aplicar migrações pendentes já existentes.
