import { useEffect, useMemo, useState } from "react";
import {
  intersectParamSchemaKeys,
  isFetchableDataBlockType,
  listDataSourceBlocks,
  resolveInputParamSchemaField,
  type ComunicadoInputBlock,
} from "@delpi/tv-dashboard-presentation";
import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";

import { listDataRoutes, type TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataParamFields, type DataParamSchema } from "./DataParamFields";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  pane?: boolean;
};

function schemasForTargets(
  routes: TvDataRouteCatalogItem[],
  operationIds: string[],
): DataParamSchema[] {
  return operationIds
    .map((operationId) => {
      const route = routes.find((item) => item.operationId === operationId);
      return (route?.paramSchema ?? {}) as DataParamSchema;
    })
    .filter((schema) => Object.keys(schema).length > 0);
}

export function InputBindingInspector({ pane = false }: Props) {
  const { selected, config, patchInputBlock } = useComunicadoEditor();
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);

  useEffect(() => {
    void listDataRoutes().then(setRoutes).catch(() => setRoutes([]));
  }, []);

  const block = selected?.type === "input" ? (selected as ComunicadoInputBlock) : null;

  const fetchable = useMemo(
    () => (config.blocks ?? []).filter((item) => isFetchableDataBlockType(item.type)),
    [config.blocks],
  );

  const targetScope = block?.input?.targetScope === "sources" ? "sources" : "slide";
  const targetSourceIds = block?.input?.targetSourceIds ?? [];

  const targetBlocks = useMemo(() => {
    if (!block) return [];
    if (targetScope === "slide") return fetchable;
    const idSet = new Set(targetSourceIds);
    return fetchable.filter((item) => idSet.has(item.id));
  }, [block, fetchable, targetScope, targetSourceIds]);

  const operationIds = useMemo(
    () =>
      targetBlocks
        .map((item) =>
          "dataBinding" in item && item.dataBinding?.operationId
            ? item.dataBinding.operationId
            : "",
        )
        .filter(Boolean),
    [targetBlocks],
  );

  const schemas = useMemo(() => schemasForTargets(routes, operationIds), [routes, operationIds]);
  const paramKeys = useMemo(() => intersectParamSchemaKeys(schemas), [schemas]);
  const field = useMemo(
    () =>
      block?.input?.paramKey
        ? resolveInputParamSchemaField(block.input.paramKey, schemas)
        : null,
    [block?.input?.paramKey, schemas],
  );

  if (!block) return null;

  const sources = listDataSourceBlocks(config.blocks ?? []);

  const applyInputPatch = (patch: Partial<ComunicadoInputBlock["input"]>) => {
    patchInputBlock(block.id, patch);
  };

  const singleSchema: DataParamSchema =
    field && block.input.paramKey ? { [block.input.paramKey]: field } : {};

  const labelByKey = (key: string): string => {
    for (const schema of schemas) {
      const label = schema[key]?.label;
      if (typeof label === "string" && label.trim()) return label;
    }
    return key;
  };

  return (
    <DeckPropertySection
      pane={pane}
      title="Campo / Filtro"
      hint="Parâmetro limitado ao schema das rotas das fontes alvo. Opções vêm da api-delpi."
    >
      {fetchable.length === 0 ? (
        <p className="td-deck-inspector__hint">Inclua uma fonte de dados no slide antes de configurar o filtro.</p>
      ) : null}

      <DeckField id="td-input-scope" label="Alvo">
        <FormSelectControl
          id="td-input-scope"
          ariaLabel="Alvo do filtro"
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          value={targetScope}
          onChange={(value) =>
            applyInputPatch({
              targetScope: value === "sources" ? "sources" : "slide",
              targetSourceIds: value === "sources" ? targetSourceIds : undefined,
            })
          }
          options={[
            { value: "slide", label: "Todo o slide" },
            { value: "sources", label: "Fontes selecionadas" },
          ]}
        />
      </DeckField>

      {targetScope === "sources" ? (
        <fieldset className="td-deck-inspector__fieldset">
          <legend className="td-deck-inspector__legend">Fontes</legend>
          {sources.length === 0 ? (
            <p className="td-deck-inspector__hint">Nenhuma fonte no slide.</p>
          ) : (
            sources.map((source) => {
              const checked = targetSourceIds.includes(source.id);
              const label = source.dataBinding?.label || source.dataBinding?.operationId || source.id;
              return (
                <label key={source.id} className="td-deck-inspector__checkbox">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={(event) => {
                      const next = event.target.checked
                        ? [...targetSourceIds, source.id]
                        : targetSourceIds.filter((id) => id !== source.id);
                      applyInputPatch({ targetSourceIds: next, targetScope: "sources" });
                    }}
                  />
                  {label}
                </label>
              );
            })
          )}
        </fieldset>
      ) : null}

      <DeckField
        id="td-input-param"
        label="Parâmetro"
        hint={
          paramKeys.length === 0
            ? "Nenhum parâmetro em comum nas fontes alvo (interseção vazia)."
            : "Somente chaves do paramSchema das rotas alvo."
        }
      >
        <FormSelectControl
          id="td-input-param"
          ariaLabel="Parâmetro da rota"
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          value={block.input.paramKey || ""}
          onChange={(value) => applyInputPatch({ paramKey: value, defaultValue: null })}
          options={[
            { value: "", label: "Selecione…" },
            ...paramKeys.map((key) => ({
              value: key,
              label: labelByKey(key),
            })),
          ]}
        />
      </DeckField>

      <DeckField id="td-input-label" label="Rótulo (opcional)">
        <NativeTextControl
          id="td-input-label"
          value={block.input.label ?? ""}
          onChange={(value) => applyInputPatch({ label: value.trim() || undefined })}
        />
      </DeckField>

      {block.input.paramKey && field ? (
        <DataParamFields
          schema={singleSchema}
          values={{ [block.input.paramKey]: block.input.defaultValue }}
          idPrefix="td-input-value"
          onChange={(_key, raw) => {
            const fieldType = field.type;
            let parsed: string | number | boolean | null = null;
            if (raw === "" || raw === null || raw === undefined) parsed = null;
            else if (fieldType === "integer" || fieldType === "number") parsed = Number(raw);
            else if (fieldType === "boolean") parsed = raw === "true";
            else parsed = String(raw).trim();
            applyInputPatch({ defaultValue: parsed });
          }}
        />
      ) : null}
    </DeckPropertySection>
  );
}
