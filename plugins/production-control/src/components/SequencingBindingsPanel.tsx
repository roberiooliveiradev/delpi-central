import { Link2, Unlink } from "lucide-react";
import { useMemo, useState } from "react";

import { copy } from "../content/copy";
import type { SequencingBinding, SequencingProfile } from "../types";

export type WorkCenterOption = {
  work_center: string;
  work_center_name: string;
};

type Props = {
  workCenters: WorkCenterOption[];
  bindings: SequencingBinding[];
  profiles: SequencingProfile[];
  branch: string;
  readOnly: boolean;
  saving: boolean;
  onBind: (workCenter: string, profileId: string | null) => void;
};

type Row = {
  work_center: string;
  work_center_name: string;
  binding: SequencingBinding | null;
};

export function SequencingBindingsPanel({
  workCenters,
  bindings,
  profiles,
  branch,
  readOnly,
  saving,
  onBind,
}: Props) {
  const texts = copy.sequencingProfiles.bindings;
  const [pending, setPending] = useState<Record<string, string>>({});

  const profileById = useMemo(
    () => new Map(profiles.map((profile) => [profile.id, profile])),
    [profiles],
  );
  const bindingByCenter = useMemo(
    () => new Map(bindings.map((binding) => [binding.work_center, binding])),
    [bindings],
  );

  /** CTs = fila do Carga-Máquina ∪ CTs já vinculados (mesmo fora da fila). */
  const rows = useMemo<Row[]>(() => {
    const seen = new Map<string, Row>();
    for (const center of workCenters) {
      seen.set(center.work_center, {
        work_center: center.work_center,
        work_center_name: center.work_center_name,
        binding: bindingByCenter.get(center.work_center) ?? null,
      });
    }
    for (const binding of bindings) {
      if (!seen.has(binding.work_center)) {
        seen.set(binding.work_center, {
          work_center: binding.work_center,
          work_center_name: "",
          binding,
        });
      }
    }
    return [...seen.values()].sort((a, b) =>
      a.work_center.localeCompare(b.work_center, "pt-BR"),
    );
  }, [workCenters, bindings, bindingByCenter]);

  /** Perfis vinculáveis: ativos e criados nesta filial (cross-branch pendente). */
  const bindable = useMemo(
    () =>
      profiles.filter(
        (profile) =>
          profile.status === "active" &&
          (!profile.origin_branch || profile.origin_branch === branch),
      ),
    [profiles, branch],
  );

  const disabled = readOnly || saving;

  const handleSelect = (row: Row, profileId: string) => {
    setPending((prev) => ({ ...prev, [row.work_center]: profileId }));
  };

  const handleApply = (row: Row) => {
    const chosen = pending[row.work_center];
    if (!chosen || chosen === row.binding?.profile_id) return;
    onBind(row.work_center, chosen);
    setPending((prev) => {
      const next = { ...prev };
      delete next[row.work_center];
      return next;
    });
  };

  const handleUnbind = (row: Row) => {
    onBind(row.work_center, null);
  };

  return (
    <section className="seq-card" aria-label={texts.title}>
      <header className="seq-card__head">
        <h3>{texts.title}</h3>
        <span className="seq-card__hint">{texts.subtitle}</span>
      </header>
      {rows.length === 0 ? (
        <p className="ppc-state">{texts.empty}</p>
      ) : (
        <ul className="seq-bindings">
          {rows.map((row) => {
            const bound = row.binding ? profileById.get(row.binding.profile_id) : null;
            const boundInactive = bound && bound.status !== "active";
            const chosen = pending[row.work_center] ?? row.binding?.profile_id ?? "";
            const dirty = chosen !== (row.binding?.profile_id ?? "");
            return (
              <li key={row.work_center} className="seq-bindings__row">
                <div className="seq-bindings__center">
                  <strong>{row.work_center}</strong>
                  {row.work_center_name ? (
                    <span>{row.work_center_name}</span>
                  ) : (
                    <span className="seq-bindings__out">{texts.outOfQueue}</span>
                  )}
                </div>
                <div className="seq-bindings__current">
                  {row.binding ? (
                    <>
                      <span>{bound?.name ?? row.binding.profile_id}</span>
                      {boundInactive ? (
                        <span className="seq-editor__warning" role="alert">
                          {texts.inactiveBound}
                        </span>
                      ) : null}
                    </>
                  ) : (
                    <span className="seq-bindings__none">{texts.unbound}</span>
                  )}
                </div>
                <div className="seq-bindings__actions">
                  <select
                    className="seq-input seq-bindings__select"
                    value={chosen}
                    disabled={disabled}
                    aria-label={texts.selectAria(row.work_center)}
                    onChange={(event) => handleSelect(row, event.target.value)}
                  >
                    <option value="">{texts.chooseProfile}</option>
                    {row.binding && boundInactive ? (
                      <option value={row.binding.profile_id}>
                        {bound?.name ?? row.binding.profile_id} ({texts.inactive})
                      </option>
                    ) : null}
                    {bindable.map((profile) => (
                      <option key={profile.id} value={profile.id}>
                        {profile.name}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    className="seq-btn"
                    disabled={disabled || !dirty}
                    onClick={() => handleApply(row)}
                  >
                    <Link2 size={15} aria-hidden /> {texts.apply}
                  </button>
                  {row.binding ? (
                    <button
                      type="button"
                      className="ppc-icon-btn"
                      disabled={disabled}
                      title={texts.unbind}
                      aria-label={`${texts.unbind} ${row.work_center}`}
                      onClick={() => handleUnbind(row)}
                    >
                      <Unlink size={16} aria-hidden />
                    </button>
                  ) : null}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
