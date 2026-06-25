import { ExternalLink } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { fetchKaizenLinkOptions, kaizenEditPath } from "../api/kaizenLinkApi";
import type { KaizenLinkSummary } from "../types/kaizenLink";
import { SelectField } from "./ui/SelectField";

type Props = {
  branchCode: string;
  value: string;
  onChange: (kaizenId: string) => void;
  disabled?: boolean;
};

export function KaizenLinkField({ branchCode, value, onChange, disabled }: Props) {
  const [items, setItems] = useState<KaizenLinkSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError(null);
    void fetchKaizenLinkOptions(branchCode)
      .then((response) => {
        if (!cancelled) setItems(response.items ?? []);
      })
      .catch((err) => {
        if (!cancelled) {
          setItems([]);
          setLoadError(err instanceof Error ? err.message : "Erro ao carregar kaizens.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [branchCode]);

  const options = useMemo(
    () =>
      items.map((item) => ({
        value: item.id,
        label: `${item.title} (${item.status})`,
      })),
    [items],
  );

  const selected = items.find((item) => item.id === value);

  return (
    <div className="pac-kaizen-link-field">
      <SelectField
        id="pac-detail-linked-kaizen"
        label="Kaizen vinculado"
        options={options}
        value={value}
        onChange={onChange}
        placeholder={loading ? "Carregando kaizens…" : "Selecione um kaizen"}
        searchable
        allowEmpty
        emptyLabel="Sem vínculo"
        disabled={disabled || loading}
      />
      {loadError ? <p className="pac-muted pac-field-hint">{loadError}</p> : null}
      {selected ? (
        <a
          className="pac-inline-link"
          href={kaizenEditPath(selected.id)}
          target="_blank"
          rel="noreferrer"
        >
          <ExternalLink size={14} />
          Abrir kaizen no cadastro
        </a>
      ) : null}
    </div>
  );
}
