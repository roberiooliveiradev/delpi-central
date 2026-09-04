# Runbook IAM — permissões legadas `invoice-issuance.*` → `my-requests.*`

Operação **manual** no Core (papéis / usuários). **Não** há script de revoke em massa neste repositório.

Mapa canônico: [PLAYBOOK.md §20.5](./PLAYBOOK.md). Retenção de schema/volume: [MIGRATION-RUNBOOK.md](./MIGRATION-RUNBOOK.md).

## Pré-requisitos

1. Soft/hard cutover feitos (E12–E13): menu oculto, redirect, MFE fora do Compose.
2. Operadores usam `/apps/my-requests` no dia a dia.
3. Gate UI live em [PARITY-P0.md](./PARITY-P0.md) preferencialmente assinado (itens 1–2).
4. Janela comunicada ao suporte / donos de papéis (Faturamento + solicitantes).

## Mapa 1:1

| Legado | Canônico | Notas |
|--------|----------|-------|
| `invoice-issuance.access` | `my-requests.access` | Abrir o app |
| `invoice-issuance.create` | `my-requests.invoice-issuance.create` | Wizard / criar NF |
| `invoice-issuance.view` | `my-requests.view-all` (se existia visão global) ou filiais | Avaliar caso a caso |
| `invoice-issuance.view.filial-01` | `my-requests.view.filial-01` | SC |
| `invoice-issuance.view.filial-02` | `my-requests.view.filial-02` | ES |
| `invoice-issuance.process` | `my-requests.invoice-issuance.process` | Fila / processar |
| `invoice-issuance.manage` | `my-requests.manage` | Admin tipos + ações excepcionais |

Manifesto canônico: `plugins/my-requests/my-requests.manifest.json`.

## Ordem segura

```text
1) Inventariar quem tem invoice-issuance.*
2) Conceder equivalentes my-requests.* (sem remover legado ainda)
3) Validar login: Minhas / Fila / Nova NF / Admin (se manage)
4) Revogar invoice-issuance.* nos papéis
5) (Opcional) arquivar permissões no catálogo Core após soak
```

### 1) Inventário (exemplos SQL — ajustar nomes reais do schema Core)

```sql
-- Substitua schema/tabelas pelos nomes do Core em produção.
-- Objetivo: listar subject (user/role) × permission code legado.

SELECT r.name AS role_name, p.code AS permission_code
  FROM core.role_permissions rp
  JOIN core.roles r ON r.id = rp.role_id
  JOIN core.permissions p ON p.id = rp.permission_id
 WHERE p.code LIKE 'invoice-issuance.%'
 ORDER BY 1, 2;

SELECT u.email, p.code
  FROM core.user_permissions up
  JOIN core.users u ON u.id = up.user_id
  JOIN core.permissions p ON p.id = up.permission_id
 WHERE p.code LIKE 'invoice-issuance.%'
 ORDER BY 1, 2;
```

Se o Core expuser UI de papéis: exportar CSV / print da tela e anexar ao ticket da janela.

### 2) Conceder canônico

Para cada papel/usuário do inventário, garantir o conjunto `my-requests.*` correspondente (tabela acima).  
Solicitante típico: `access` + `view.filial-*` + `invoice-issuance.create`.  
Faturamento: + `invoice-issuance.process`.  
Admin módulo: + `manage`.

### 3) Validação

| Perfil | Checagem |
|--------|----------|
| Solicitante | `/apps/my-requests/new?type=invoice-issuance` cria; aparece em Minhas |
| Processador | Fila lista itens; start/return/complete |
| Manage | `/apps/my-requests/admin` lista tipos |

### 4) Revogar legado

Remover `invoice-issuance.*` dos papéis **somente** após validação.  
Não revogar em produção sem janela e rollback (re-conceder legado se necessário).

### 5) Soak

Manter permissões legadas no catálogo (códigos) por pelo menos uma janela de suporte; remoção do catálogo Core é opcional e fora deste runbook.

## O que NÃO fazer

- Revoke automático / job sem inventário.
- Remover lookups api-delpi ou `DROP SCHEMA invoice_issuance` neste passo.
- Assumir que `invoice-issuance.view` ≡ `my-requests.view-all` sem checar o papel.

## Registro

| Ambiente | Data | Executado por | Papéis alterados | Observação |
|----------|------|---------------|------------------|------------|
| | | | | |

## Referências

- [PLAYBOOK.md §20.5](./PLAYBOOK.md)
- [MIGRATION-RUNBOOK.md](./MIGRATION-RUNBOOK.md)
- [PARITY-P0.md](./PARITY-P0.md)
- [MANUAL-USUARIO.md](./MANUAL-USUARIO.md)
