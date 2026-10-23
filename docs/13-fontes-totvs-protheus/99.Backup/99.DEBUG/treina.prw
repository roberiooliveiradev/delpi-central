
cSql :=""

cSql +="SELECT TOP 20  B2_FILIAL,	B2_QFIM,	B2_LOCAL,	B2_QATU,B2_CM1,B2_VFIM1"
cSql +="INTO #TEMP"
cSql +="FROM dbo.SB2T10 (NOLOCK) TBL1 "
cSql +="WHERE TBL1.D_E_L_E_T_ = ''"

If Select('TMPQRY') <> 0
    TMPQRY->(dbCloseArea())
Endif
TCQuery cSql Alias TMPQRY New

WHILE  TMPQRY->(!eof())


    TMPQRY->(dbSkip())
EndDo
