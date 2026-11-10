import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { itPortalApi, type Page } from "../../api/itPortalApi";
import { ItpSelectField, ItpTextField } from "../../app/itPortalUi";
import { useDebouncedValue } from "../../app/useDebouncedValue";
import { DBMS_LABELS } from "../../content/labels";

export type PickerKind = "server" | "service" | "database";

type Option = { value: string; label: string };

const PICKER_PAGE_SIZE = 50;

/** Somente cadastros ativos podem receber vínculos — o backend revalida (409 se arquivado). */
async function fetchOptions(kind: PickerKind, q: string, signal: AbortSignal): Promise<Page<Option>> {
  const query = { q: q || undefined, archived: "active" as const, sort: "name", page_size: PICKER_PAGE_SIZE };
  if (kind === "server") {
    const page = await itPortalApi.listServers(query, signal);
    return { ...page, items: page.items.map((s) => ({ value: s.id, label: `${s.code} · ${s.name} (${s.hostname})` })) };
  }
  if (kind === "service") {
    const page = await itPortalApi.listServices(query, signal);
    return { ...page, items: page.items.map((s) => ({ value: s.id, label: `${s.code} · ${s.name}` })) };
  }
  const page = await itPortalApi.listDatabases(query, signal);
  return {
    ...page,
    items: page.items.map((d) => ({
      value: d.id,
      label: `${d.code} · ${d.name} (${DBMS_LABELS[d.dbms]} em ${d.server.name})`,
    })),
  };
}

const PICKER_COPY: Record<PickerKind, { search: string; select: string }> = {
  server: { search: "Buscar servidor", select: "Servidor" },
  service: { search: "Buscar serviço", select: "Serviço" },
  database: { search: "Buscar instância de banco", select: "Instância de banco" },
};

export function ResourcePicker({
  kind,
  value,
  onChange,
  excludeIds = [],
  initialOption,
}: {
  kind: PickerKind;
  value: string;
  onChange: (value: string) => void;
  excludeIds?: readonly string[];
  initialOption?: Option;
}) {
  const [search, setSearch] = useState("");
  const q = useDebouncedValue(search);
  const optionsQuery = useQuery({
    queryKey: ["it-portal", "picker", kind, q],
    queryFn: ({ signal }) => fetchOptions(kind, q, signal),
    placeholderData: keepPreviousData,
  });
  const copy = PICKER_COPY[kind];
  const loaded = (optionsQuery.data?.items ?? []).filter((option) => !excludeIds.includes(option.value));
  const options =
    initialOption && !loaded.some((option) => option.value === initialOption.value)
      ? [initialOption, ...loaded]
      : loaded;
  const total = optionsQuery.data?.total ?? 0;
  const hint = optionsQuery.isError
    ? "Não foi possível carregar a lista. Tente buscar novamente."
    : total > PICKER_PAGE_SIZE
      ? `Mostrando ${PICKER_PAGE_SIZE} de ${total} cadastros ativos. Refine a busca pelo nome.`
      : "Somente cadastros ativos podem ser vinculados.";

  return (
    <>
      <ItpTextField type="search" label={copy.search} value={search} onChange={setSearch} placeholder="Digite parte do nome…" />
      <ItpSelectField
        label={copy.select}
        hint={hint}
        options={options}
        value={value}
        onChange={onChange}
        searchable
        required
        disabled={optionsQuery.isPending}
      />
    </>
  );
}
