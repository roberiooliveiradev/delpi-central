class ConsumptionRealQuantityService:
    SQL_EXPRESSION = """
        CASE
          WHEN D4.D4_QTDEORI > D4.D4_QUANT
          THEN D4.D4_QTDEORI - D4.D4_QUANT
          ELSE 0
        END
    """
