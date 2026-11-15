objetivo: Adicionar o cupom FRETEGRATIS no checkout da loja.
RQ-1: o cupom FRETEGRATIS zera o frete do pedido e não dá desconto no subtotal.
AC-1: checkout_total(itens, região, "FRETEGRATIS") == subtotal(itens) para qualquer região válida.
AC-2: cupom desconhecido continua levantando ValueError (em apply_coupon e em checkout_total).
AC-3: testes automatizados cobrindo AC-1 (pelo menos duas regiões) e AC-2.
AC-4: DESC10 continua funcionando como antes.
RQ-2: FRETEGRATIS pode ser combinado com DESC10 conforme a política comercial.
