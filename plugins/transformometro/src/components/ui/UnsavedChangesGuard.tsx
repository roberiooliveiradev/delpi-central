import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  type ReactNode,
} from "react";

import {
  unsavedChangesDialogOptions,
  useConfirmChoice,
} from "./ConfirmDialogProvider";
import { resolveUnsavedLeave } from "../../utils/unsavedChangesLeave";

export type UnsavedChangesGuardRegistration = {
  id: string;
  /** Seção em modo edição (lock / EditableSectionCard aberto). */
  isEditing: () => boolean;
  /** Há diferenças em relação ao baseline. */
  isDirty: () => boolean;
  save: () => Promise<void>;
  discard: () => void;
};

type UnsavedChangesGuardContextValue = {
  register: (registration: UnsavedChangesGuardRegistration) => () => void;
  /** Retorna true se a navegação pode seguir. */
  confirmLeave: () => Promise<boolean>;
  guardedNavigate: (href: string, navigate: (path: string) => void) => Promise<void>;
};

const UnsavedChangesGuardContext = createContext<UnsavedChangesGuardContextValue | null>(
  null,
);

export function UnsavedChangesGuardProvider({ children }: { children: ReactNode }) {
  const confirmChoice = useConfirmChoice();
  const guardsRef = useRef(new Map<string, UnsavedChangesGuardRegistration>());

  const register = useCallback((registration: UnsavedChangesGuardRegistration) => {
    guardsRef.current.set(registration.id, registration);
    return () => {
      guardsRef.current.delete(registration.id);
    };
  }, []);

  const confirmLeave = useCallback(async () => {
    return resolveUnsavedLeave(Array.from(guardsRef.current.values()), () =>
      confirmChoice(unsavedChangesDialogOptions()),
    );
  }, [confirmChoice]);

  const guardedNavigate = useCallback(
    async (href: string, navigate: (path: string) => void) => {
      const allowed = await confirmLeave();
      if (allowed) navigate(href);
    },
    [confirmLeave],
  );

  const value = useMemo(
    () => ({ register, confirmLeave, guardedNavigate }),
    [confirmLeave, guardedNavigate, register],
  );

  return (
    <UnsavedChangesGuardContext.Provider value={value}>
      {children}
    </UnsavedChangesGuardContext.Provider>
  );
}

export function useUnsavedChangesGuardContext() {
  const context = useContext(UnsavedChangesGuardContext);
  if (!context) {
    throw new Error(
      "useUnsavedChangesGuardContext deve ser usado dentro de UnsavedChangesGuardProvider",
    );
  }
  return context;
}

/** Opcional: páginas fora do provider não quebram (ex.: testes isolados). */
export function useOptionalUnsavedChangesGuard() {
  return useContext(UnsavedChangesGuardContext);
}

type UseUnsavedChangesGuardOptions = {
  id: string;
  editing: boolean;
  dirty: boolean;
  onSave: () => Promise<void>;
  onDiscard: () => void;
  enabled?: boolean;
};

/**
 * Registra um editor com dirty check para o guard de navegação do plugin.
 */
export function useUnsavedChangesGuard({
  id,
  editing,
  dirty,
  onSave,
  onDiscard,
  enabled = true,
}: UseUnsavedChangesGuardOptions) {
  const context = useOptionalUnsavedChangesGuard();
  const editingRef = useRef(editing);
  const dirtyRef = useRef(dirty);
  const onSaveRef = useRef(onSave);
  const onDiscardRef = useRef(onDiscard);

  editingRef.current = editing;
  dirtyRef.current = dirty;
  onSaveRef.current = onSave;
  onDiscardRef.current = onDiscard;

  useEffect(() => {
    if (!context || !enabled) return;
    return context.register({
      id,
      isEditing: () => editingRef.current,
      isDirty: () => dirtyRef.current,
      save: () => onSaveRef.current(),
      discard: () => onDiscardRef.current(),
    });
  }, [context, enabled, id]);
}

export function useGuardedNavigate(navigate: (path: string) => void) {
  const context = useOptionalUnsavedChangesGuard();
  return useCallback(
    (href: string) => {
      if (!context) {
        navigate(href);
        return;
      }
      void context.guardedNavigate(href, navigate);
    },
    [context, navigate],
  );
}
