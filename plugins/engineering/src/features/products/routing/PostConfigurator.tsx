/** Routing Study V2 — organização hipotética da linha (`Configurar
 * postos`). Cada posto é um card do kit com nome editável,
 * multisseleção de operações oficiais, CTs/recursos derivados da
 * seleção (a fonte vincula CT/recurso à operação — selecionar o CT
 * livremente criaria associação inexistente), operadores e posições
 * paralelas propostos e ordenação por botões (acessível por teclado).
 *
 * Tudo aqui é `DRAFT_LOCAL / SIMULATION`: o motor atual não valida
 * alocação por posto, precedência ou paralelismo — a limitação é
 * exibida de forma explícita e nada é enviado ao contrato
 * `line-balance`. */

import { ArrowDown, ArrowUp, Trash2 } from "lucide-react";

import {
  EngineeringActionButton,
  EngineeringDetailCard,
  EngineeringDetailFieldGrid,
  EngineeringIconButton,
  EngineeringMultiSelectField,
  EngineeringTextAreaField,
  EngineeringTextField,
} from "../../../ui/engineeringUi";
import type { HypotheticalPost } from "./routingStudyDraft";
import type { RoutingOperationView } from "./routingGrouping";

function parsePositiveInt(text: string): number | null {
  const n = Number(text.trim().replace(",", "."));
  return Number.isFinite(n) && n > 0 ? Math.floor(n) : null;
}

function PostCard({
  post,
  index,
  total,
  operations,
  disabled,
  onPatch,
  onMove,
  onRemove,
}: {
  post: HypotheticalPost;
  index: number;
  total: number;
  operations: RoutingOperationView[];
  disabled?: boolean;
  onPatch: (patch: Partial<HypotheticalPost>) => void;
  onMove: (direction: -1 | 1) => void;
  onRemove: () => void;
}) {
  const options = operations.map((op) => ({
    value: op.key,
    label: `${op.operation_code || "—"} — ${op.operation_description ?? "—"}`,
  }));
  const selected = new Set(post.operationRefs);
  const selectedOps = operations.filter((o) => selected.has(o.key));
  const workCenters = [...new Set(selectedOps.map((o) => o.work_center).filter(Boolean))];
  const resources = [...new Set(selectedOps.map((o) => o.resource_code).filter(Boolean))];

  return (
    <EngineeringDetailCard
      title={post.name || `Posto ${String(index + 1).padStart(2, "0")}`}
      titleHint="Posto hipotético do estudo — não é um cadastro oficial nem prova de posto físico."
      headerActions={
        <div
          className="engineering-routing__post-actions"
          role="group"
          aria-label={`Ações do ${post.name}`}
        >
          <EngineeringIconButton
            aria-label={`Mover ${post.name} para cima`}
            disabled={disabled || index === 0}
            onClick={() => onMove(-1)}
          >
            <ArrowUp size={16} aria-hidden="true" />
          </EngineeringIconButton>
          <EngineeringIconButton
            aria-label={`Mover ${post.name} para baixo`}
            disabled={disabled || index === total - 1}
            onClick={() => onMove(1)}
          >
            <ArrowDown size={16} aria-hidden="true" />
          </EngineeringIconButton>
          <EngineeringIconButton
            aria-label={`Remover ${post.name}`}
            tone="danger"
            disabled={disabled}
            onClick={onRemove}
          >
            <Trash2 size={16} aria-hidden="true" />
          </EngineeringIconButton>
        </div>
      }
    >
      <div className="engineering-routing__post-grid">
        <EngineeringTextField
          id={`post-name-${post.clientId}`}
          label="Nome do posto"
          value={post.name}
          onChange={(v) => onPatch({ name: v })}
          disabled={disabled}
        />
        <EngineeringMultiSelectField
          label="Operações atribuídas"
          options={options}
          selectedValues={post.operationRefs}
          onChange={(refs) => onPatch({ operationRefs: refs })}
          hint="Somente operações oficiais do estágio selecionado podem ser vinculadas."
          searchable
          disabled={disabled || !operations.length}
        />
        <EngineeringTextField
          id={`post-ops-${post.clientId}`}
          label="Operadores propostos"
          value={post.operators != null ? String(post.operators) : ""}
          onChange={(v) => onPatch({ operators: parsePositiveInt(v) })}
          hint="Hipótese — não validada pelo motor atual."
          disabled={disabled}
        />
        <EngineeringTextField
          id={`post-par-${post.clientId}`}
          label="Posições paralelas"
          value={post.parallelPositions != null ? String(post.parallelPositions) : ""}
          onChange={(v) => onPatch({ parallelPositions: parsePositiveInt(v) })}
          hint="Hipótese — não inferida da quantidade de CTs."
          disabled={disabled}
        />
      </div>
      <EngineeringDetailFieldGrid
        fields={[
          {
            label: "CTs associados",
            value: workCenters.length ? workCenters.join(" · ") : "—",
            hint: "Derivados das operações selecionadas — CT não equivale a posto físico.",
          },
          {
            label: "Recursos associados",
            value: resources.length ? resources.join(" · ") : "—",
            hint: "Derivados das operações selecionadas — não prova disponibilidade simultânea.",
          },
          {
            label: "Ordem no estudo",
            value: String(index + 1),
            hint: "Sequência hipotética — não altera a ordem oficial do roteiro.",
          },
        ]}
      />
      <EngineeringTextAreaField
        id={`post-note-${post.clientId}`}
        label="Observações do estudo"
        value={post.note}
        onChange={(v) => onPatch({ note: v })}
        rows={2}
        disabled={disabled}
      />
    </EngineeringDetailCard>
  );
}

export function PostConfigurator({
  posts,
  operations,
  maxPosts,
  disabled,
  onAdd,
  onPatch,
  onMove,
  onRemove,
}: {
  posts: HypotheticalPost[];
  operations: RoutingOperationView[];
  maxPosts: number;
  disabled?: boolean;
  onAdd: () => void;
  onPatch: (clientId: string, patch: Partial<HypotheticalPost>) => void;
  onMove: (clientId: string, direction: -1 | 1) => void;
  onRemove: (clientId: string) => void;
}) {
  return (
    <div
      className="engineering-routing__posts"
      role="group"
      aria-label="Postos hipotéticos do estudo"
    >
      {posts.map((post, i) => (
        <PostCard
          key={post.clientId}
          post={post}
          index={i}
          total={posts.length}
          operations={operations}
          disabled={disabled}
          onPatch={(patch) => onPatch(post.clientId, patch)}
          onMove={(dir) => onMove(post.clientId, dir)}
          onRemove={() => onRemove(post.clientId)}
        />
      ))}
      <EngineeringActionButton
        variant="default"
        disabled={disabled || posts.length >= maxPosts}
        onClick={onAdd}
      >
        Adicionar posto
      </EngineeringActionButton>
    </div>
  );
}
