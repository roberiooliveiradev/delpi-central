from app.database import get_connection
from app.models.cliente_model import Cliente

def get_clientes(limite: int = 10) -> list[Cliente]:
    conn = get_connection()
    cursor = conn.cursor()

    query = f"""
    SELECT TOP {limite}
        A1_COD AS codigo,
        A1_NOME AS nome,
        A1_EST AS uf,
        A1_CGC AS cnpj
    FROM SA1010
    WHERE D_E_L_E_T_ = ''
    ORDER BY A1_NOME
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    colunas = [desc[0].lower() for desc in cursor.description]

    clientes = [Cliente(**dict(zip(colunas, row))) for row in rows]

    cursor.close()
    conn.close()

    return clientes
