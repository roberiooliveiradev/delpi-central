# ATLAS | Etapa 74: tmpfiles sem correção silenciosa e auditoria de conflitos

**18/11/2026 | Issue #232 | source-only | status=blocked | PREPARE/ACT OFF**

## Por que esta etapa

A etapa 73 preparou cinco regras d em tmpfiles, ainda não instaladas.
Pela semântica do systemd, as regras d comuns podem reaplicar modo,
usuário e grupo em diretórios que já existam. Isso poderia mascarar drift
de permissões no boot. A etapa 74 usa a forma create-only, prefixo :
nos três campos mode, user e group. Se o inode já existir, esses
atributos NÃO são reparados automaticamente. O preflight posterior deve
rejeitar owner, grupo, setgid, ACL ou inode incompatíveis.

Referência primária: https://www.freedesktop.org/software/systemd/man/latest/tmpfiles.d.html

## Pacote consolidado

- Mantém os arquivos de candidatos não instaláveis, com o layout tmpfiles
  agora using create-only em todos os cinco diretórios fixos.
- Atualiza os revisores e negativas das etapas 70 e 73 para recusar
  candidatos permissivos, conflitos de GID e quaisquer regras extras.
- Adiciona atlas_hml_b_stage74_tmpfiles_audit.py, auditor somente leitura
  que identifica regras concorrentes nas quatro localizações tmpfiles.d,
  detecta symlinks, arquivos instáveis, duplicidade de nome, operações
  contra diretórios ATLAS e unidades systemd já presentes.
- A CLI exige explicitamente fixture descartável ou --host-readonly,
  nunca habilita serviços e sempre entrega status=blocked.
- Testes exercitam efeitos reais de systemd-tmpfiles SOMENTE com --root
  apontando para pasta de fixture do runner GitHub. O teste cria diretório
  isolado, muda o modo para 0777 e confirma que a segunda execução
  não repõe 0750. Nenhum teste usa a raiz / do runner para criar regras.

## Limites honestos de evidência

A leitura de arquivos tmpfiles em diretórios padrão NÃO demonstra toda
a configuração efetiva, nem pesquisa todos os perfis, drop-ins, aliases,
transient units, atributos de segurança e endpoints Docker. Aplicar
tmpfiles no sistema real é outra mudança com risco próprio. Diretórios
preexistentes com modo incorreto não são corrigidos, mas a própria regra
create-only pode retornar sucesso: o fail-closed dependerá de preflight
após criação e do bloqueio operacional do serviço em caso de drift.
O auditor é self-observation, sem independência de Security.

Nenhum pull, deploy, instalação, systemd, reboot, keygen, docker.socket,
mudança de grupos/permissões, ou chamada ao host srv-api é realizada aqui.

## Próxima janela C, ainda NÃO autorizada para instalação

1. Confirmar merge da PR e revisão independente do pacote no SHA exato.
2. Rodar leitura de baseline e auditor com autorização para coleta HML.
3. Verificar conflitos entre regras tmpfiles efetivas e unidades instaladas;
   inventariar AppArmor, aliases de Docker e FDs herdados do ambiente real.
4. Elaborar plano de instalação com arquivo .conf revisado e bloqueio pós-boot,
   teste de reboot/rollback e baseline PROD antes/depois.
5. Só então, solicitar autorização operacional específica de janela,
   comandos, responsável e rollback. Sem PREPARE/ACT até SEC-01..10.

**Sem aumento artificial de progresso:** ATLAS geral continua 60%,
e Etapa 74 concluída em código apenas após aprovação do CI e Verifier.
