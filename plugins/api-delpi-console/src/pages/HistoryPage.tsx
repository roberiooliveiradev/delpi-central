import { useMemo, useState } from "react";
import { Trash2 } from "lucide-react";
import { clearHistory, listHistory } from "../lib/requestHistory";

type Props = {
  onNavigate: (path: string) => void;
};

export function HistoryPage({ onNavigate }: Props) {
  const [entries, setEntries] = useState(() => listHistory());
  const [filter, setFilter] = useState("");

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return entries;
    return entries.filter(
      (e) =>
        e.path.toLowerCase().includes(q) ||
        e.method.toLowerCase().includes(q) ||
        String(e.status).includes(q) ||
        (e.operationIdHeader ?? "").toLowerCase().includes(q),
    );
  }, [entries, filter]);

  const handleClear = () => {
    clearHistory();
    setEntries([]);
  };

  return (
    <div className="adc-page">
      <header className="adc-header adc-header--compact">
        <div>
          <button type="button" className="adc-link" onClick={() => onNavigate("")}>
            ← Início
          </button>
          <h1>Histórico de chamadas</h1>
          <p className="adc-subtitle">Últimas {entries.length} requisições (localStorage).</p>
        </div>
        <button type="button" className="adc-btn adc-btn--ghost" onClick={handleClear}>
          <Trash2 size={16} />
          Limpar
        </button>
      </header>

      <input
        className="adc-input"
        type="search"
        placeholder="Filtrar por path, status, operation id…"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
      />

      {filtered.length === 0 ? (
        <div className="adc-panel adc-muted">Nenhuma chamada registrada ainda.</div>
      ) : (
        <div className="adc-table-wrap">
          <table className="adc-table">
            <thead>
              <tr>
                <th>Quando</th>
                <th>Método</th>
                <th>Path</th>
                <th>Status</th>
                <th>Cliente ms</th>
                <th>Servidor ms</th>
                <th>Operation Id</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((e) => (
                <tr key={e.id}>
                  <td>{new Date(e.timestamp).toLocaleString("pt-BR")}</td>
                  <td>
                    <span className={`adc-method adc-method--${e.method.toLowerCase()}`}>
                      {e.method}
                    </span>
                  </td>
                  <td>
                    <code>{e.path}</code>
                  </td>
                  <td>
                    <span className={e.ok ? "adc-ok" : "adc-err"}>{e.status}</span>
                  </td>
                  <td>{e.durationMs}</td>
                  <td>{e.responseTimeHeader ?? "—"}</td>
                  <td>
                    <code className="adc-mono-sm">{e.operationIdHeader ?? "—"}</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
