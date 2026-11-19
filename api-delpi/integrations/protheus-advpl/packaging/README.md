# packaging — pacotes de compilação determinísticos

`package.py` gera um ZIP **byte-reprodutível** a partir de um **commit aprovado**
do `delpi-central` — nunca do working tree. Não há conectividade ERP, execução
ADVPL ou interação com RPO.

## Uso

```bash
python3 package.py \
  --repo /path/delpi-central --commit <sha-aprovado> \
  --module product-master --module product-suppliers \
  --version 0.1.0 --target-env TST01 --out-dir packaging/out
python3 package.py --check packaging/out/<pkg>.zip   # re-hash vs manifest.json
```

## Contrato

- Somente `modules/<id>/src/*` **declarados** em `contracts/module.yaml`
  (`sources:`) entram como `source`; `.prw`/`.tlpp` não declarados = erro.
- `contracts/**` entram como `contract`; docs `.md` fora de `src/` como `doc`.
- Rejeita: módulo ausente, `module.yaml` incompleto, fonte declarado ausente,
  fonte não declarado, path traversal, symlink/submodule, `.env`/secrets/keys.
- `created_at` = timestamp do commit (determinismo); ZIP com nomes ordenados,
  data fixa, sem extras → mesmo commit+conteúdo = mesmo SHA-256.
- `manifest.json` embutido segue `manifest.schema.json`; nome do pacote é
  rótulo — autoridade é o SHA.
- Saída em `packaging/out/` (git-ignored). **Nunca commitar ZIPs.**

## Limites

Este script **não** compila, publica ou valida runtime. Compilação/homologação
é handoff para a equipe ERP (`handoffs/`).
