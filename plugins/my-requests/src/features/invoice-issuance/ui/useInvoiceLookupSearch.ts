import { useCallback, useRef } from "react";

import type { EntityDirectoryOption } from "@delpi/plugin-ui/index";

import {
  carrierEntityId,
  carrierToOption,
  partyEntityId,
  partyToOption,
  productEntityId,
  productToOption,
} from "../domain/entityLookupMappers";
import type { Carrier, Party, PartyType, ProductHit } from "../domain/types";
import { searchCarriers, searchParties, searchProducts } from "../lookupsApi";

type SearchFn = (
  query: string,
  limit?: number,
  signal?: AbortSignal,
) => Promise<EntityDirectoryOption[]>;

/**
 * Mapeia lookups do wizard NF → EntityDirectoryOption, com cache para
 * recuperar a entidade completa a partir do id do chip.
 */
export function useInvoiceLookupSearch(partyType: PartyType) {
  const partiesById = useRef(new Map<string, Party>());
  const productsById = useRef(new Map<string, ProductHit>());
  const carriersById = useRef(new Map<string, Carrier>());

  const rememberParty = useCallback((party: Party) => {
    partiesById.current.set(partyEntityId(party), party);
  }, []);

  const rememberProduct = useCallback((product: ProductHit) => {
    productsById.current.set(productEntityId(product), product);
  }, []);

  const rememberCarrier = useCallback((carrier: Carrier) => {
    carriersById.current.set(carrierEntityId(carrier), carrier);
  }, []);

  const searchPartyEntities: SearchFn = useCallback(
    async (query, limit, signal) => {
      const items = await searchParties(partyType, query, limit ?? 10, signal);
      for (const item of items) rememberParty(item);
      return items.map(partyToOption);
    },
    [partyType, rememberParty],
  );

  const searchProductEntities: SearchFn = useCallback(async (query, limit, signal) => {
    const items = await searchProducts(query, limit ?? 10, signal);
    for (const item of items) rememberProduct(item);
    return items.map(productToOption);
  }, [rememberProduct]);

  const searchCarrierEntities: SearchFn = useCallback(async (query, limit, signal) => {
    const items = await searchCarriers(query, limit ?? 10, signal);
    for (const item of items) rememberCarrier(item);
    return items.map(carrierToOption);
  }, [rememberCarrier]);

  const resolveParty = useCallback(
    (id: string) => partiesById.current.get(id) ?? null,
    [],
  );
  const resolveProduct = useCallback(
    (id: string) => productsById.current.get(id) ?? null,
    [],
  );
  const resolveCarrier = useCallback(
    (id: string) => carriersById.current.get(id) ?? null,
    [],
  );

  return {
    searchPartyEntities,
    searchProductEntities,
    searchCarrierEntities,
    resolveParty,
    resolveProduct,
    resolveCarrier,
    rememberParty,
    rememberProduct,
    rememberCarrier,
  };
}
