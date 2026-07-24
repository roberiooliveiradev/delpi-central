-- Apresentação do número da nota com 9 dígitos (zeros à esquerda).
-- document_number VARCHAR(9) já comporta; alinha registros gravados com pad de 8.

UPDATE lancamento_notas_fiscais.invoice_posting_requests
SET document_number = lpad(regexp_replace(document_number, '\D', '', 'g'), 9, '0')
WHERE length(regexp_replace(document_number, '\D', '', 'g')) BETWEEN 1 AND 8;
