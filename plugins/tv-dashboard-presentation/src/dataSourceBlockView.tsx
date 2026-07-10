import { Database } from "lucide-react";

import { resolveDataSourceLabel } from "./comunicadoDataArchitecture";
import type { ComunicadoDataSourceBlock } from "./comunicadoTypes";

type Props = {
  block: ComunicadoDataSourceBlock;
  interactive?: boolean;
  loading?: boolean;
  /** Palco do editor — ícone de banco de dados. */
  editorMode?: boolean;
};

export function DataSourceBlockView({ block, interactive = false, loading = false, editorMode = false }: Props) {
  const label = resolveDataSourceLabel(block);
  const resolved = block.resolved;

  if (resolved?.error) {
    return (
      <div className="tdp-data-block tdp-data-block--error tdp-data-source">
        <Database size={28} aria-hidden="true" />
        <span>{String(resolved.error)}</span>
      </div>
    );
  }

  if (editorMode || interactive) {
    return (
      <div
        className={`tdp-data-source tdp-data-source--editor${loading ? " tdp-data-block--loading" : ""}`}
        title={label}
      >
        <Database size={32} strokeWidth={1.75} aria-hidden="true" />
        <span className="tdp-data-source__label">{label}</span>
        {loading ? <span className="tdp-data-source__hint">Carregando…</span> : null}
      </div>
    );
  }

  return null;
}
