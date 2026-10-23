/*/{Protheus.doc}  OM010MNU
(long_description)
@type  Function
@author Gabriel
@since 02/12/2020
@version version
@param param_name, param_type, param_descr
@return return_var, return_type, return_description
@example
(examples)
@see (links_or_references)
/*/
user Function  OM010MNU()

    aadd(aRotina,{'Log Proces','U_dlpLogP()' , 0 , 3,0,NIL})

Return


User function dlpLogP()
    Local cProcLog  :="OMSA010_DLP"
    ProcLogView(,cProcLog)
Return
