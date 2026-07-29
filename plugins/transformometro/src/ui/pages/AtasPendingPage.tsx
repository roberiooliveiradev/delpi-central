import { useEffect, useState } from "react";
import { ActionButton } from "@delpi/plugin-ui/index";
import type { AppProps } from "../../App";
import { TransformometroShell } from "../../components/TransformometroShell";
import { buildAtaSignPath } from "../../constants/routes";
import { pendingAtas, type AtaListItem } from "../../data/api/transformometroAtaApi";

type Props = Pick<AppProps, "getAccessToken"> & { onNavigate: (path: string) => void };
export function AtasPendingPage({ getAccessToken, onNavigate }: Props) {
  const [items, setItems] = useState<AtaListItem[]>([]); const [error, setError] = useState<string | null>(null);
  useEffect(() => { void pendingAtas(getAccessToken).then((data) => setItems(data.items)).catch((value) => setError(value instanceof Error ? value.message : "Erro ao carregar pendências.")); }, [getAccessToken]);
  return <TransformometroShell><section className="ds-card"><h1>Assinaturas pendentes</h1>{error ? <p role="alert">{error}</p> : null}<ul>{items.map((item) => <li key={item.id}>{item.meeting_date} · {item.title} <ActionButton onClick={() => onNavigate(buildAtaSignPath(item.id))}>Assinar</ActionButton></li>)}{!items.length ? <li>Não há atas pendentes para assinatura.</li> : null}</ul></section></TransformometroShell>;
}
