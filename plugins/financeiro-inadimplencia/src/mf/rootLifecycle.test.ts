import { describe, expect, it } from "vitest";
import type { Root } from "react-dom/client";

/**
 * Espelha o ciclo mount/unmount do bootstrap sem carregar Module Federation.
 * Garante montagem única, unmount sem root órfão e remontagem.
 */
function createRootLifecycle(createRoot: (el: HTMLElement) => Root) {
  const roots = new WeakMap<HTMLElement, Root>();

  function mount(el: HTMLElement) {
    const existing = roots.get(el);
    if (existing) {
      return existing;
    }
    const root = createRoot(el);
    roots.set(el, root);
    return root;
  }

  function unmount(el?: HTMLElement) {
    if (!el) return;
    const root = roots.get(el);
    if (!root) return;
    root.unmount();
    roots.delete(el);
  }

  function has(el: HTMLElement) {
    return roots.has(el);
  }

  return { mount, unmount, has };
}

describe("ciclo mount/unmount (Module Federation)", () => {
  it("monta uma vez, desmonta sem órfão e remonta", () => {
    const el = {} as HTMLElement;
    let unmountCalls = 0;
    let created = 0;

    const lifecycle = createRootLifecycle(() => {
      created += 1;
      return {
        render: () => undefined,
        unmount: () => {
          unmountCalls += 1;
        },
      } as unknown as Root;
    });

    const first = lifecycle.mount(el);
    const second = lifecycle.mount(el);
    expect(first).toBe(second);
    expect(created).toBe(1);

    lifecycle.unmount(el);
    expect(lifecycle.has(el)).toBe(false);
    expect(unmountCalls).toBe(1);

    lifecycle.mount(el);
    expect(created).toBe(2);
    expect(lifecycle.has(el)).toBe(true);
  });
});

