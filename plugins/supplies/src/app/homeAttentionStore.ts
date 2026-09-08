import {
  getHomeAttention,
  type HomeAttentionCard,
  type HomeAttentionPartialFailure,
} from "../api/homeAttention";

export type HomeAttentionState = {
  loading: boolean;
  error: string | null;
  cards: HomeAttentionCard[];
  partialFailures: HomeAttentionPartialFailure[];
};

type Listener = (state: HomeAttentionState) => void;

const INITIAL: HomeAttentionState = {
  loading: false,
  error: null,
  cards: [],
  partialFailures: [],
};

let state: HomeAttentionState = { ...INITIAL };
let loadSeq = 0;
const listeners = new Set<Listener>();

function emit(): void {
  for (const listener of listeners) {
    listener(state);
  }
}

export function getHomeAttentionSnapshot(): HomeAttentionState {
  return state;
}

export function subscribeHomeAttention(listener: Listener): () => void {
  listeners.add(listener);
  listener(state);
  return () => {
    listeners.delete(listener);
  };
}

export async function loadHomeAttention(signal?: AbortSignal): Promise<HomeAttentionState> {
  const seq = ++loadSeq;
  state = { ...state, loading: true, error: null };
  emit();
  try {
    const payload = await getHomeAttention(signal);
    if (seq !== loadSeq) return state;
    if (signal?.aborted) {
      state = { ...state, loading: false };
      emit();
      return state;
    }
    state = {
      loading: false,
      error: null,
      cards: Array.isArray(payload.cards) ? payload.cards : [],
      partialFailures: Array.isArray(payload.partialFailures) ? payload.partialFailures : [],
    };
    emit();
    return state;
  } catch (error: unknown) {
    if (seq !== loadSeq) return state;
    if (signal?.aborted) {
      state = { ...state, loading: false };
      emit();
      return state;
    }
    const message =
      error instanceof Error && error.message.trim()
        ? error.message
        : "Não foi possível carregar a atenção.";
    state = {
      loading: false,
      error: message,
      cards: [],
      partialFailures: [],
    };
    emit();
    return state;
  }
}

export function resetHomeAttentionStoreForTests(): void {
  loadSeq += 1;
  state = { ...INITIAL };
  listeners.clear();
}
