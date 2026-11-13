import { useQuery } from "@tanstack/react-query";
import { useId, useState } from "react";

import { searchDirectoryUsers } from "../../api/coreDirectoryApi";
import { useDebouncedValue } from "../../app/useDebouncedValue";

export function WorkstationOwnerPicker({
  selectedId,
  selectedName,
  legacyName,
  disabled = false,
  onSelect,
}: {
  selectedId: string | null;
  selectedName: string;
  legacyName?: string | null;
  disabled?: boolean;
  onSelect: (id: string | null, name: string) => void;
}) {
  const inputId = useId();
  const [search, setSearch] = useState(selectedId ? selectedName : "");
  const debounced = useDebouncedValue(search.trim(), 350);
  const browsing = !selectedId && debounced.length >= 2;
  const results = useQuery({
    queryKey: ["it-portal", "directory-users", debounced],
    queryFn: ({ signal }) => searchDirectoryUsers(debounced, signal),
    enabled: browsing && !disabled,
    staleTime: 30_000,
  });

  return (
    <div className="itp-owner-picker">
      <label htmlFor={inputId}>Responsável (colaborador da plataforma)</label>
      <div className="itp-owner-picker__controls">
        <input
          id={inputId}
          type="search"
          autoComplete="off"
          value={search}
          disabled={disabled}
          onChange={(event) => {
            setSearch(event.target.value);
            if (selectedId || legacyName) onSelect(null, "");
          }}
          placeholder="Digite ao menos 2 letras para localizar o colaborador"
          aria-describedby={`${inputId}-help`}
        />
        <button
          type="button"
          disabled={disabled || (!selectedId && !legacyName && !search)}
          onClick={() => {
            setSearch("");
            onSelect(null, "");
          }}
        >
          Sem responsável
        </button>
      </div>
      <p id={`${inputId}-help`} className="itp-muted">
        {selectedId
          ? "Usuário vinculado pelo identificador do Core. Troque pela busca ou remova a atribuição."
          : legacyName
            ? `Cadastro anterior (texto): ${legacyName}. Selecione o usuário correspondente para criar o vínculo.`
            : "Apenas escolher um resultado vincula o colaborador. Texto digitado não é salvo."}
      </p>
      {browsing && !disabled ? (
        <div className="itp-owner-picker__results">
          {results.isFetching ? <p className="itp-muted" role="status">Buscando colaboradores…</p> : null}
          {results.isError ? <p role="alert">Não foi possível consultar os usuários. Tente novamente.</p> : null}
          {results.isSuccess && results.data.length === 0 ? <p className="itp-muted">Nenhum colaborador encontrado.</p> : null}
          {results.isSuccess && results.data.length > 0 ? (
            <div role="listbox" aria-label="Colaboradores encontrados">
              {results.data.map((person) => (
                <button
                  key={person.id}
                  type="button"
                  role="option"
                  aria-selected={false}
                  onClick={() => {
                    onSelect(person.id, person.name);
                    setSearch(person.name);
                  }}
                >
                  <strong>{person.name}</strong>
                  {person.email ? <span className="itp-muted">{person.email}</span> : null}
                </button>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
