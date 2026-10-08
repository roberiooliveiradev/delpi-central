/**
 * Palette search (G3 / IG-1) — UI de produto sobre a palette vendor.
 *
 * GOVERNANÇA: a lista de entries vem de `adapter.paletteEntries()` — o
 * inventário REAL da paleta depois do filtro fail-closed do editingProfile.
 * A busca não carrega catálogo paralelo de capabilities: só pode oferecer
 * o que a paleta já oferece (CREATE_EDIT). Aliases abaixo são metadados de
 * apresentação (termos PT-BR/EN que resolvem para entries existentes) —
 * nunca adicionam capacidade nova.
 *
 * Ativação = mesmo path do clique do usuário (`triggerEntry` no adapter):
 * entra na interação de create existente (drag→clique posiciona).
 */
import { useEffect, useMemo, useRef, useState } from "react";
import type { BpmnEditorAdapter } from "../editor/BpmnEditorAdapter";

type Entry = { id: string; title: string };

/** Termos de busca por entry id — apresentação, não capability. */
const SEARCH_ALIASES: Record<string, string[]> = {
  "create.start-event": ["inicio", "início", "start", "evento de inicio"],
  "create.intermediate-event": [
    "intermediario",
    "timer",
    "mensagem",
    "boundary",
    "borda",
  ],
  "create.end-event": ["fim", "end", "termino", "término", "final"],
  "create.exclusive-gateway": ["gateway", "xor", "exclusivo", "decisao", "decisão"],
  "create.task": [
    "tarefa",
    "task",
    "atividade",
    "usuario",
    "usuário",
    "servico",
    "serviço",
    "manual",
    "regra",
  ],
  "create.subprocess-expanded": ["subprocesso", "sub processo", "sub-processo"],
  "create.data-object": ["objeto de dados", "data object", "dado"],
  "create.data-store": ["repositorio", "repositório", "data store"],
  "create.participant-expanded": ["pool", "raia", "lane", "participante"],
  "create.group": ["grupo", "agrupamento"],
};

function normalize(s: string): string {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");
}

function matches(entry: Entry, term: string): boolean {
  const t = normalize(term).trim();
  if (!t) return false;
  const hay = [entry.title, entry.id, ...(SEARCH_ALIASES[entry.id] ?? [])].map(
    normalize,
  );
  return hay.some((h) => h.includes(t));
}

export function PaletteSearch({
  adapter,
}: {
  adapter: BpmnEditorAdapter | null;
}) {
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const listId = "bpmnm-palette-search-list";

  // entries lidas no momento da busca — a paleta só está populada após o
  // import; chamar a cada render/query mantém o resultado sempre atual.
  const results = useMemo(
    () =>
      open && adapter
        ? adapter.paletteEntries().filter((e) => matches(e, query))
        : [],
    [adapter, query, open],
  );

  // "/" abre a busca quando o foco não está em campo de texto.
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key !== "/" || e.ctrlKey || e.metaKey || e.altKey) return;
      const t = e.target as HTMLElement | null;
      if (
        t &&
        (t.tagName === "INPUT" ||
          t.tagName === "TEXTAREA" ||
          t.isContentEditable)
      ) {
        return;
      }
      e.preventDefault();
      inputRef.current?.focus();
      setOpen(true);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const activate = (entry: Entry) => {
    adapter?.activatePaletteEntry(entry.id);
    setQuery("");
    setOpen(false);
    inputRef.current?.blur();
  };

  return (
    <div className="bpmnm-palette-search">
      <input
        ref={inputRef}
        type="text"
        role="combobox"
        aria-expanded={open && results.length > 0}
        aria-controls={listId}
        aria-activedescendant={
          open && results[active] ? `${listId}-${active}` : undefined
        }
        aria-label="Buscar na paleta"
        className="bpmnm-palette-search__input"
        placeholder="Buscar elemento… ( / )"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setActive(0);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={(e) => {
          if (e.key === "Escape") {
            setQuery("");
            setOpen(false);
            inputRef.current?.blur();
            return;
          }
          if (e.key === "ArrowDown") {
            e.preventDefault();
            setActive((i) => Math.min(i + 1, results.length - 1));
          } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setActive((i) => Math.max(i - 1, 0));
          } else if (e.key === "Enter" && results[active]) {
            e.preventDefault();
            activate(results[active]);
          }
        }}
      />
      {open && query.trim() && (
        <ul
          id={listId}
          role="listbox"
          aria-label="Resultados da paleta"
          className="bpmnm-palette-search__results"
        >
          {results.length === 0 ? (
            <li className="bpmnm-palette-search__empty">Nenhum resultado</li>
          ) : (
            results.map((entry, i) => (
              <li
                key={entry.id}
                id={`${listId}-${i}`}
                role="option"
                aria-selected={i === active}
                className={
                  i === active
                    ? "bpmnm-palette-search__option is-active"
                    : "bpmnm-palette-search__option"
                }
                onMouseEnter={() => setActive(i)}
                onMouseDown={(e) => {
                  e.preventDefault();
                  activate(entry);
                }}
              >
                {entry.title}
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
