/*/{Protheus.doc} F4LOTIND
(long_description)
@type  Function
@author Gabriel
@since 03/04/2025
@version version
@param param_name, param_type, param_descr
@return return_var, return_type, return_description
@example
(examples)
@see (links_or_references)
/*/
user Function F4LOTIND()
    Local aLotes:= PARAMIXB[1]

    aSort(aLotes ,,, { |x,y| x[7] < y[7] } )

Return aLotes
