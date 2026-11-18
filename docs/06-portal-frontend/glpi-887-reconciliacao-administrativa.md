# GLPI #887 - Vincular cadastros RH e Minha Delpi

## Por que simplificamos

A primeira versão do painel exigia muitos passos: checkbox, redigitar a
matrícula, inserir referência e passar por um diálogo de confirmação.
Para o administrador que conhece os cadastros, isso tornou a operação
desnecessariamente difícil.

Esta entrega reduz o fluxo à tarefa principal: **selecionar a pessoa RH,
selecionar a conta Core e confirmar o vínculo**.

## Como usar

1. Abra `Administração > Vincular cadastros` (aba `identity`).
   A equipe de matrícula `20001` abre automaticamente, com a opção
   `Equipe completa` ativada. É possível informar outra matrícula de gestor.
2. As pendências vêm primeiro, com as sugestões por nome no topo.
   Clique **Vincular** no colaborador desejado.
3. O portal busca automaticamente contas com o nome do colaborador.
   Se não aparecer, altere o termo para parte do nome ou e-mail e clique **Buscar**.
4. Clique na conta correta na lista (nome + e-mail).
5. Clique em **Vincular conta**, compare os dois nomes/matrícula/e-mail no
   diálogo e confirme **Sim, vincular**. O vínculo é gravado e a lista atualiza.

Não há checkbox adicional, redigitação de matrícula, campo de justificativa
ou ação em lote. O usuário administrador realiza **uma confirmação objetiva**
para cada associação.

## Segurança que continua existindo

- Backend exige JWT e as permissões `rbac.manage` **e** `users.manage`.
- A prévia `identity-review` está disponível apenas a administradores
  autorizados; nomes e e-mails não são expostos publicamente.
- Nome coincidente é **só uma sugestão**, nunca associação automática.
  O administrador precisa conferir visualmente o titular antes de confirmar.
- O backend mantém `confirmIdentity=true`, verificação do colaborador no
  RH oficial, conta Core ativa, prevenção de matrícula duplicada e evento de
  auditoria com identidade do administrador, antes/depois, data e IP.
- Antes do PUT, a interface também impede a operação caso a conta Core
  esteja vinculada a outra matrícula.
- O campo de referência de evidência do backend **continua opcional** para
  outras ferramentas, sem alterar o contrato; a nova interface não o exige.
- Sem alteração de dados até o clique final; sem importação/associação em lote,
  sem novo agendamento, sem envio de e-mails e sem mudança no Portal RH.

## Situação observada em produção em 18/11/2026

Para o gestor `20001`, última apuração recebida:
- 63 colaboradores RH ativos na equipe completa.
- 0 vínculos RH ↔ Core verificados.
- 8 sugestões apenas por nome e 55 sem sugestão.

Esses números são anteriores às associações que o usuário poderá fazer no
painel. `Sem sugestão` não significa `sem conta Minha Delpi`.

## Publicação

Esta PR modifica **somente o frontend `portal`** do monorepo
`delpi-central`, não altera migrations, Core API nem o Portal RH.
O usuário é o único responsável por aprovar/fazer merge.
Atualizar o checkout com segurança, preservar mudanças locais e reconstruir
somente o serviço `portal` depois do merge autorizado.

Os relatórios semanais individuais permanecem condicionados a identidades
Core verificadas, consentimento de rastreamento e autorização de
destinatários conforme LGPD. Nenhum envio automático foi habilitado.
