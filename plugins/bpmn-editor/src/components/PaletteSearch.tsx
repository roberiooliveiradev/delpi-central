/**
 * Palette search (G3 / IG-1; roteamento semântico G3-PAL-1) — UI de produto.
 *
 * GOVERNANÇA: os resultados vêm de `adapter.searchCreateActions()` — a
 * projeção CREATE_EDIT exportada por `editingProfile.ts` (mesma autoridade
 * que governa palette/context-pad/replace/clipboard). Não há catálogo
 * paralelo de capabilities.
 *
 * ROTEAMENTO SEMÂNTICO: cada resultado promete o QName que cria. Constructs
 * tipados sem entry direta na palette usam CREATE_THEN_REPLACE — o adapter
 * aplica o replace governado após o usuário posicionar o elemento. Aliases
 * apontam apenas para o mesmo significado do resultado: "usuário" →
 * Tarefa de Usuário (bpmn:UserTask), nunca para Tarefa genérica.
 *
 * Constructs contextuais (Lane, BoundaryEvent) e preserve-only não são
 * listados — não existe create path global governado para eles.
 *
 * Ativação = mesmo path do clique do usuário (`triggerEntry` no adapter):
 * entra na interação de create existente (drag→clique posiciona).
 */
import { useEffect, useMemo, useRef, useState } from "react";
import type { BpmnEditorAdapter } from "../editor/BpmnEditorAdapter";
import type { SearchableCreateAction } from "../editor/editingProfile";

function normalize(s: string): string {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");
}

function matches(action: SearchableCreateAction, term: string): boolean {
  const t = normalize(term).trim();
  if (!t) return false;
  const hay = [action.label, action.id, ...action.aliases].map(normalize);
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

  // ações lidas a cada query — o inventário é estável por sessão, mas ler
  // sob demanda mantém o resultado consistente com o profile vigente.
  const results = useMemo(
    () =>
      open && adapter && query.trim()
        ? adapter.searchCreateActions().filter((a) => matches(a, query))
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

  const activate = (action: SearchableCreateAction) => {
    adapter?.activateSearchCreateAction(action.id);
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
            results.map((action, i) => (
              <li
                key={action.id}
                id={`${listId}-${i}`}
                role="option"
                aria-selected={i === active}
                className={
                  i === active
                    ? "bpmnm-palette-search__option is-active"
                    : "bpmnm-palette-search__option"
                }
                onMouseEnter={() => setActive(i)}
                // click (não mousedown): o create-drag do vendor arma em
                // triggerEntry; ativar durante mousedown faz o mouseup do
                // próprio clique ser consumido como drop prematuro sobre
                // o dropdown. click dispara após o mouseup → drag limpo.
                onClick={() => activate(action)}
              >
                {action.label}
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
