"""TÉO specialist intelligence + canonical capability registry.

capability_registry is the single inward source for capability↔transport
bindings; transport_projection derives per-transport projections from it.
Adapters (GPT Actions HTTP, MCP) consume these — never the reverse.
"""
