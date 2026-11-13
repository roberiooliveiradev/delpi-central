# Delpi Remote | Convencao de identificacao de computadores (proposta)

**Data:** 2026-11-13 | **Estado:** proposta para validacao no primeiro cadastro piloto, ainda sem mudanca automatica de hostname.

## Formato recomendado para campo Nome

```text
DLP-<UF>-<SETOR>-<TNN>
```

- `DLP`: empresa.
- `UF`: `SC` (matriz Santa Catarina) ou `ES` (filial Espirito Santo).
- `SETOR`: sigla curta e documentada do setor, em geral 2 ou 3 letras (por exemplo `TI`, `PCP`, `ENG`, `RH`).
- `T`: tipo, `D` desktop ou `N` notebook. Outros tipos exigem classificacao documentada antes de uso.
- `NN`: sequencia de 2 digitos por combinacao de unidade/setor/tipo, atribuida por TI, sem reutilizacao imediata de numeros.

**Exemplos ficticios:** `DLP-ES-TI-D01`, `DLP-SC-ENG-N01`, `DLP-ES-PCP-D02`.

**Importante:** estes nomes identificam o ativo no Portal, **nao** alteram o hostname do Windows. O campo `Hostname` deve conter o valor real retornado por `$env:COMPUTERNAME`. Se a Delpi optar por renomear computadores no futuro, validar impacto em dominio, DNS, impressoras, certificados, aplicativos, inventario/MDM e Windows antes de executar uma mudanca coordenada.

## Diferentes identificadores

- `code` gerado pelo Portal (exemplo `PC-0001`): referencia imutavel de apresentacao do cadastro, definida pelo banco; **nao** escolher manualmente.
- `id` UUID interno: identidade persistente para integracoes.
- `name`: nomenclatura operacional proposta `DLP-<UF>-<SETOR>-<TNN>`.
- `hostname`: nome real do Windows, nao deve ser inventado ou automaticamente trocado na etapa G1.
- IP privado: dado mutavel de inventario, nunca chave de identidade do equipamento. IP publico de outra interface ou de VPN nao deve ser registrado sem atribuicao/validacao.
- Numero de serie do fabricante: registrar somente em area restrita do inventario corporativo e conforme politica de privacidade da empresa. Nao publicar em issue ou repositorio publico.

## Primeiro piloto de homologacao

- Estacao proposta: desktop corporativo da TI na filial ES, com nome operacional candidato `DLP-ES-TI-D01`.
- Coleta inicial feita manualmente via PowerShell Windows; equipamento/usuario ainda **nao** validados como cadastrado em producao.
- IP, hostname real, serial e outras informacoes reais da estacao nao sao reproduzidos aqui, pois este repositorio e publico.
- Antes de aceitar a nomenclatura como padrao definitivo: confirmar setor, unidade, unicidade da sequencia e cadastro criado no Portal.
- Validar fluxo G1: salvar, localizar, abrir ficha, editar, verificar auditoria, arquivar e restaurar. Testar tambem acesso negado por RBAC em conta sem permissao.

## Regras para a evolucao G2

- Nao usar nome, IP, MAC ou serial isoladamente para autenticar o agente remoto.
- Separar identidade criptografica da estacao e do operador humano.
- Nao sobrescrever `name` curado com hostname obtido automaticamente.
- Se houver divergencia de dados, mostrar alerta para reconciliacao manual.

**Revisao:** proposta inicial do responsavel de TI, sujeita a aprovacao apos o primeiro cadastro piloto; registrar eventual mudanca aqui e no diario de execucao.
