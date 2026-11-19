# GLPI #887 | Vinculação RH ↔ Core sem hierarquia

## Diagnóstico

A antiga aba Administração > Vincular cadastros iniciava pela matrícula
`20001` e carregava somente os colaboradores **subordinados** ao gestor
informado. O gestor raiz não entrava na lista. Mesmo ao informar `10257`
(CEO), a tela exibiria seus subordinados, mas não o próprio CEO.

O backend já tinha o contrato individual seguro e auditado:

```http
PUT /admin/organization/users/{core_user_uuid}/hr-registration
{ "registration": "10257", "confirmIdentity": true }
```

Esse endpoint **já** consulta `GET /api/v1/integrations/collaborators/{registration}/`
no Portal RH, verifica a situação de atividade e impede vínculos conflitantes.
Não precisa de migração e não permite vínculos automáticos.

A aba/frontend havia sido removida de `main` por alteração concorrente
`40caeb1` em 18/11/2026, embora estivesse funcional no ambiente
compilado anterior. Esta PR restaura a aba, substituindo a dependência
da equipe de gestor por um diretório de contas Core.

## Novo fluxo

1. Acesse Administração > **Vincular cadastros**.
2. A tela mostra **todas as contas Minha Delpi (Core)**, ativas e inativas,
   ordenadas por nome, com matrícula RH vinculada quando houver.
   A origem desta lista é Core, não uma subárvore de gestores.
3. O filtro `Ativas pendentes` vem selecionado por padrão; também há
   filtros `Vinculadas` e `Todas as contas`.
4. Digite parte do nome/e-mail para encontrar a conta do CEO.
5. Clique `Vincular`, informe **10257**, clique `Consultar RH` e
   confira o registro oficial `DENNIS GIORGIO PICCOLI` e a filial.
6. Confirme individualmente que a conta Core e a pessoa RH são a
   mesma identidade. O PUT existente faz a associação auditada.
7. A tela recarrega e marca a conta como vinculada.
8. Nenhuma outra conta ou matrícula é alterada.

**Limite semântico:** "todas as pessoas" neste painel significa
todas as **contas do Minha Delpi/Core**. O Portal RH não possui,
na integração S2S desta entrega, um endpoint verificado de catálogo
global de colaboradores. Para colaboradores ainda sem conta Core,
será necessário criar/associar a conta por processo existente.
A busca individual de RH é exata e não depende de gestor.

## Endpoints novos, ambos exclusivos para administração

Exigem simultaneamente `rbac.manage` + `users.manage` (ou superadmin):

```http
GET /admin/organization/identity-directory
GET /admin/organization/collaborators/{registration}/identity-preview
```

O primeiro consulta **somente** contas Core e suas matrículas
existentes; não acessa hierarquia RH nem altera vínculos. O segundo
usa a API oficial RH para validar nome, matrícula, filial e situação,
sem expor dados pessoais adicionais. Ambos possuem rate limit.

Vínculos anteriores são preservados, sem backfill, alteração de senha,
RBAC, login, consentimentos ou histórico. O endpoint PUT permanece
protegido por confirmação humana e trilha de auditoria. A simples
semelhança de nomes nunca autoriza vínculo.

**Invariante:** o diretório é somente um recurso administrativo para
vincular contas. Ele NÃO substitui as regras de envio dos relatórios,
que continuam exigindo hierarquia RH oficial, subordinados diretos,
consentimento, vínculo Core verificado e destinatário único.

## Validação e publicação

Após merge autorizado e pré-verificação de arquivos locais:

```bash
cd /home/operador/projetos/delpi-central
git status --short
git pull --ff-only origin main

# Simular primeiro, sem tocar serviços
bash ./infra/scripts/up-prod-sequential.sh --dry-run --fase core --build core-api portal

# Depois de aprovar o plano e a janela de manutenção
bash ./infra/scripts/up-prod-sequential.sh --fase core --build core-api portal
```

Apenas `core-api` e `portal` mudam, sem migrações. Sem alterações
na API Delpi ou MFE Reports. A aplicação deve ser testada pela aba
Administração após o rebuild do portal. O `core-api` deve estar
saudável antes de abrir a aba; usar a janela de manutenção autorizada.

### Critérios de aceite

- Aba `Vincular cadastros` voltou a `Administração`.
- Conta do CEO visível ao pesquisar pelo nome, sem campo de gestor.
- Perfil RH `10257` encontrado diretamente, sem buscar subordinados.
- Confirmação vincula somente conta Core escolhida.
- Outras matrículas já vinculadas permanecem como estavam.
- Usuários sem permissão de administração recebem 403.
- Não há disparo de relatórios nem mudança de agendamento.

## Retomada dos relatórios

Antes da alteração, na raiz `10257` foram identificados
12 gestores elegíveis por relação direta no RH:
- 7 definições já existentes;
- 4 pendentes para `prepare_disabled`;
- CEO matrícula `10257` em `missing_mapping`.

Após confirmar a vinculação do CEO, repetir a consulta **read-only**
para verificar que sua situação migrou para `prepare_disabled`:

```bash
docker exec delpi-api-delpi python \
  -m app.scripts.glpi_887_prepare_manager_reports --root 10257
```

Não rodar `--apply` antes de confirmar a lista do novo escopo.
`REPORTS_DIRECT_WEEKLY_DELIVERY_ENABLED` permanece `false`.
Nenhuma mudança de envio ou agenda é solicitada por esta PR.

## Testes

```bash
cd core-api
pytest app/tests/test_glpi_887_global_identity_directory.py \
       app/tests/test_portal_rh_organization.py -q
cd ../portal
npm run build
```

Testes versionados estão incluídos, mas devem ser executados pelo CI.
