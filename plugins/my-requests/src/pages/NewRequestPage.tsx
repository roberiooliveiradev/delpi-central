import { useEffect, useState, type FormEvent } from "react";

import { createRequest, listRequestTypes } from "../api/requestsApi";
import { AppShell } from "../components/AppShell";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import type { RequestTypeSummary } from "../types/requests";

export function NewRequestPage() {
  const access = useRequestsPermissions();
  const [types, setTypes] = useState<RequestTypeSummary[]>([]);
  const [typeCode, setTypeCode] = useState("");
  const [branchCode, setBranchCode] = useState(access.branches[0] || "01");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const ac = new AbortController();
    listRequestTypes({ signal: ac.signal })
      .then((items) => {
        setTypes(items);
        if (items[0]?.code) setTypeCode(items[0].code);
      })
      .catch((err: Error) => {
        if (err.name !== "AbortError") setError(err.message);
      });
    return () => ac.abort();
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!typeCode) return;
    setBusy(true);
    setError(null);
    try {
      const created = await createRequest({
        typeCode,
        branchCode,
        idempotencyKey: crypto.randomUUID(),
        payload: {},
      });
      window.location.assign(`/apps/my-requests/requests/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar");
      setBusy(false);
    }
  }

  return (
    <AppShell title="Nova solicitação" canCreate>
      <section className="dashboard-my-requests__panel" data-help="new">
        {error ? <p className="dashboard-my-requests__error">{error}</p> : null}
        <form className="dashboard-my-requests__form" onSubmit={onSubmit}>
          <label>
            Tipo
            <select
              value={typeCode}
              onChange={(e) => setTypeCode(e.target.value)}
              disabled={busy || types.length === 0}
            >
              {types.map((item) => (
                <option key={item.code} value={item.code}>
                  {item.name} ({item.code})
                </option>
              ))}
            </select>
          </label>
          <label>
            Filial
            <select
              value={branchCode}
              onChange={(e) => setBranchCode(e.target.value)}
              disabled={busy}
            >
              {(access.branches.length ? access.branches : ["01", "02"]).map((code) => (
                <option key={code} value={code}>
                  {code}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" className="dashboard-my-requests__btn" disabled={busy || !typeCode}>
            Criar
          </button>
        </form>
      </section>
    </AppShell>
  );
}
