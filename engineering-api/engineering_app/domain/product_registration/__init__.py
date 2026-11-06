"""Bounded context Product Registration — Controle e Cadastro de Produtos.

Domínio framework-free: solicitações de cadastro/alteração (intake),
draft técnico editável, workflow governado e verificação oficial TOTVS.

Fronteiras (PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT.md):
- Solicitação/draft/revisão/verificação pertencem à Engenharia;
- a autoridade oficial do cadastro permanece no TOTVS (leitura via
  adapter autorizado da api-delpi — nunca escrita);
- revisão publicada é imutável e nasce SOMENTE de verificação `matched`.
"""
