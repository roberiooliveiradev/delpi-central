#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"

/*
01  - Desenvolver caixa de perguntas com base no parambox
    - DA1 - Unica
    - Produto De/Ate
    - ID Calculo
    - Atualiza Tabela de Venda Sim/Nao
02  Desenvolver query para listar os produtos
03  Desenvolver Rotina para chamar o MVC
*/


user function DLP02F10()

    Local aPergs   := {}
    Local aRetPro   := {}
    Local aMvPar   := {}
    Local aRet     := {}
    Local cTabVen  := space(getsx3cache("DA0_CODTAB","X3_TAMANHO" ))
    Local cProdDe  := space(getsx3cache("B1_COD" ,"X3_TAMANHO" ))
    Local cProdAte := space(getsx3cache("B1_COD" ,"X3_TAMANHO" ))
    Local cIDSZ7   := space(getsx3cache("Z7_ID" ,"X3_TAMANHO"  ))
    Local cAtual   := "N"
    Local cVldPrc   := "N"
    Local nMv      := 0
    Local aArea    := getarea()
    Local aTam     := {20,60,60,60,60}
    Local n1 := 0
    Private aRetBox     := {}



    /*VARIAVEIS PRIVATE LEGADO*/

    Private aFiles    :={}
    Private cEol      := chr(10)
    PRIVATE lLibField := .f.
    PRIVATE lRetCx    := .f.
    Private cBox1     := "1PRD01"
    Private cBox2     := "2OPE01"
    Private  cBox3    := "3IMP01"
    Private nTmIt     := getsx3cache("Z9_ITEM","X3_TAMANHO")
    Private nTotMP    := 0 // Variavel que totaliza a Materia Prima
    Private nTotMOD   := 0 // Variavel que totaliza a Mao de Obra
    Private nTotBen   := 0 // Variavel que totaliza a Beneficiamento
    Private nTotGG    := 0 // Variavel que totaliza Gastos Gerais
    Private nQtdBas   := 1 // Variavel Quantidade Basica
    Private nTotUnit  := 0
    Private NTOTESTR  := 0
    Private LucroOper := 0
    Private nPVOper   := 0
    Private nVlFre    := 0
    Private nCoefOper := 0
    Private nCoefImp  := 0
    Private lRecal    := .f.
    Private cTabPV    := space(3)
    //Variaveis da aba impostos
    Private nICMS    :=0  // ICMS
    Private nPisCof  :=0  // PIS E COFINS
    Private nComiss  :=0  // COMISSÃO
    Private nISS     :=0  // ISS
    Private nCoef    :=0  // COEFICIENTE
    Private nPVVenda :=0  // PV VENDA
    Private nIRCSLL  :=0  // IR E CSLL
    Private nCusPrd  :=0 // Custo produto
    Private lCanAlt := .F.
    Private lVldCpos := .f.
    Private aPrdQtBas := {}
    Private aCusLiq := {0,0,0} //icms - pis cof - frete
    Private nQtdEst := 0
    /****************************/
    /****************************/
    // Private lBrowse := .T.
    Private aRotina		:= MenuDef()
    Private aLogProc := {} // ID |CODIGO PRODUTO | erro
    Private lAuto := .t.
    Private lVldPrcVd := .f.

    aIDSZ8 := {}
    //aadd(aIDSZ8,{'002127' , 3301 })
    //aadd(aIDSZ8,{'002128' , 3302 })
    //aadd(aIDSZ8,{'002130' , 3304 })
    //aadd(aIDSZ8,{'002131' , 3305 })
    //aadd(aIDSZ8,{'002132' , 3306 })
    //aadd(aIDSZ8,{'002133' , 3307 })
    //aadd(aIDSZ8,{'002134' , 3308 })
    //aadd(aIDSZ8,{'002135' , 3309 })
    //aadd(aIDSZ8,{'002136' , 3310 })
    //aadd(aIDSZ8,{'002137' , 3311 })
    //aadd(aIDSZ8,{'002138' , 3312 })
    //aadd(aIDSZ8,{'002139' , 3313 })
    //aadd(aIDSZ8,{'002141' , 3314 })
    //aadd(aIDSZ8,{'002143' , 3316 })
    //aadd(aIDSZ8,{'002144' , 3317 })
    //aadd(aIDSZ8,{'002145' , 3318 })
    //aadd(aIDSZ8,{'002146' , 3319 })
    //aadd(aIDSZ8,{'002147' , 3320 })
    //aadd(aIDSZ8,{'002148' , 3321 })
    //aadd(aIDSZ8,{'002149' , 3322 })
    //aadd(aIDSZ8,{'002150' , 3323 })
    //aadd(aIDSZ8,{'002151' , 3324 })
    //aadd(aIDSZ8,{'002152' , 3325 })
    //aadd(aIDSZ8,{'002153' , 3326 })
    //aadd(aIDSZ8,{'002155' , 3327 })
    //aadd(aIDSZ8,{'002156' , 3329 })
    //aadd(aIDSZ8,{'002157' , 3330 })
    //aadd(aIDSZ8,{'002159' , 3331 })
    //aadd(aIDSZ8,{'002160' , 3332 })
    //aadd(aIDSZ8,{'002161' , 3333 })
    //aadd(aIDSZ8,{'002162' , 3334 })
    //aadd(aIDSZ8,{'002164' , 3336 })
    //aadd(aIDSZ8,{'002165' , 3337 })
    //aadd(aIDSZ8,{'002166' , 3338 })
    //aadd(aIDSZ8,{'002169' , 3340 })
    //aadd(aIDSZ8,{'002177' , 3350 })
    //aadd(aIDSZ8,{'000884' , 2802 })
    //aadd(aIDSZ8,{'000885' , 2803 })
    //aadd(aIDSZ8,{'000886' , 2804 })
    //aadd(aIDSZ8,{'000887' , 2805 })
    //aadd(aIDSZ8,{'000888' , 2806 })
    //aadd(aIDSZ8,{'000889' , 2807 })
    //aadd(aIDSZ8,{'000890' , 2808 })
    //aadd(aIDSZ8,{'000891' , 2809 })
    //aadd(aIDSZ8,{'000892' , 2810 })
    //aadd(aIDSZ8,{'000893' , 2811 })
    //aadd(aIDSZ8,{'000894' , 2812 })
    //aadd(aIDSZ8,{'000895' , 2813 })
    //aadd(aIDSZ8,{'000896' , 2814 })
    //aadd(aIDSZ8,{'000897' , 2815 })
    //aadd(aIDSZ8,{'000898' , 2816 })
    //aadd(aIDSZ8,{'000899' , 2817 })
    //aadd(aIDSZ8,{'000900' , 2818 })
    //aadd(aIDSZ8,{'000901' , 2819 })
    //aadd(aIDSZ8,{'000902' , 2820 })
    //aadd(aIDSZ8,{'000903' , 2821 })
    //aadd(aIDSZ8,{'000904' , 2822 })
    //aadd(aIDSZ8,{'000905' , 2823 })
    //aadd(aIDSZ8,{'000906' , 2824 })
    //aadd(aIDSZ8,{'000908' , 2828 })
    //aadd(aIDSZ8,{'000909' , 2829 })
    //aadd(aIDSZ8,{'000910' , 2830 })
    //aadd(aIDSZ8,{'000911' , 2832 })
    //aadd(aIDSZ8,{'000912' , 2833 })
    //aadd(aIDSZ8,{'000913' , 2834 })
    //aadd(aIDSZ8,{'000914' , 2835 })
    //aadd(aIDSZ8,{'000916' , 2836 })
    //aadd(aIDSZ8,{'000917' , 2837 })
    //aadd(aIDSZ8,{'000918' , 2838 })
    //aadd(aIDSZ8,{'000919' , 2840 })
    //aadd(aIDSZ8,{'000920' , 2841 })
    //aadd(aIDSZ8,{'000921' , 2842 })
    //aadd(aIDSZ8,{'000922' , 2843 })
    //aadd(aIDSZ8,{'000923' , 2844 })
    //aadd(aIDSZ8,{'000924' , 2845 })
    //aadd(aIDSZ8,{'000925' , 2846 })
    //aadd(aIDSZ8,{'000926' , 2847 })
    //aadd(aIDSZ8,{'000927' , 2848 })
    //aadd(aIDSZ8,{'000928' , 2849 })
    //aadd(aIDSZ8,{'000929' , 2850 })
    //aadd(aIDSZ8,{'000932' , 2853 })
    //aadd(aIDSZ8,{'000933' , 2854 })
    //aadd(aIDSZ8,{'000934' , 2855 })
    //aadd(aIDSZ8,{'000935' , 2856 })
    //aadd(aIDSZ8,{'000936' , 2857 })
    //aadd(aIDSZ8,{'000937' , 2858 })
    //aadd(aIDSZ8,{'000938' , 2859 })
    //aadd(aIDSZ8,{'000939' , 2860 })
    //aadd(aIDSZ8,{'000940' , 2861 })
    //aadd(aIDSZ8,{'000941' , 2862 })
    //aadd(aIDSZ8,{'000942' , 2863 })
    //aadd(aIDSZ8,{'000943' , 2864 })
    //aadd(aIDSZ8,{'000944' , 2865 })
    //aadd(aIDSZ8,{'000945' , 2866 })
    //aadd(aIDSZ8,{'000947' , 2870 })
    //aadd(aIDSZ8,{'000948' , 2871 })
    //aadd(aIDSZ8,{'000949' , 2872 })
    //aadd(aIDSZ8,{'000950' , 2873 })
    //aadd(aIDSZ8,{'000951' , 2874 })
    // aadd(aIDSZ8,{'000952' , 2875 }) deu erro
    //aadd(aIDSZ8,{'000953' , 2876 })
    //aadd(aIDSZ8,{'000954' , 2878 })
    aadd(aIDSZ8,{'000955' , 2879 })
    aadd(aIDSZ8,{'000956' , 2880 })
    aadd(aIDSZ8,{'000957' , 2881 })
    aadd(aIDSZ8,{'000958' , 2882 })
    aadd(aIDSZ8,{'000959' , 2883 })
    aadd(aIDSZ8,{'000960' , 2885 })
    aadd(aIDSZ8,{'000961' , 2886 })
    aadd(aIDSZ8,{'000962' , 2887 })
    aadd(aIDSZ8,{'000963' , 2888 })
    aadd(aIDSZ8,{'000964' , 2889 })
    aadd(aIDSZ8,{'000965' , 2890 })
    aadd(aIDSZ8,{'000966' , 2891 })
    aadd(aIDSZ8,{'000967' , 2892 })
    aadd(aIDSZ8,{'000968' , 2893 })
    aadd(aIDSZ8,{'000969' , 2894 })
    aadd(aIDSZ8,{'000970' , 2895 })
    aadd(aIDSZ8,{'000971' , 2896 })
    aadd(aIDSZ8,{'000972' , 2897 })
    aadd(aIDSZ8,{'000973' , 2898 })
    aadd(aIDSZ8,{'000975' , 2900 })
    aadd(aIDSZ8,{'000976' , 2901 })
    aadd(aIDSZ8,{'000977' , 2902 })
    aadd(aIDSZ8,{'000978' , 2903 })
    aadd(aIDSZ8,{'000979' , 2904 })
    aadd(aIDSZ8,{'000980' , 2905 })
    aadd(aIDSZ8,{'000981' , 2906 })
    aadd(aIDSZ8,{'000982' , 2907 })
    aadd(aIDSZ8,{'000983' , 2908 })
    aadd(aIDSZ8,{'000984' , 2909 })
    aadd(aIDSZ8,{'000985' , 2910 })
    aadd(aIDSZ8,{'000986' , 2911 })
    aadd(aIDSZ8,{'000987' , 2912 })
    aadd(aIDSZ8,{'000988' , 2913 })
    aadd(aIDSZ8,{'000989' , 2914 })
    aadd(aIDSZ8,{'000991' , 2915 })
    aadd(aIDSZ8,{'000992' , 2916 })
    aadd(aIDSZ8,{'000993' , 2917 })
    aadd(aIDSZ8,{'000994' , 2919 })
    aadd(aIDSZ8,{'000995' , 2920 })
    aadd(aIDSZ8,{'000996' , 2921 })
    aadd(aIDSZ8,{'000998' , 2923 })
    aadd(aIDSZ8,{'001000' , 2924 })
    aadd(aIDSZ8,{'001001' , 2926 })
    aadd(aIDSZ8,{'001011' , 2938 })
    aadd(aIDSZ8,{'001012' , 2940 })
    aadd(aIDSZ8,{'001013' , 2941 })
    aadd(aIDSZ8,{'001015' , 2943 })
    aadd(aIDSZ8,{'001016' , 2944 })
    aadd(aIDSZ8,{'001017' , 2945 })
    aadd(aIDSZ8,{'001018' , 2946 })
    aadd(aIDSZ8,{'001019' , 2947 })
    aadd(aIDSZ8,{'001020' , 2948 })
    aadd(aIDSZ8,{'001021' , 2949 })
    aadd(aIDSZ8,{'001022' , 2950 })
    aadd(aIDSZ8,{'001023' , 2951 })
    aadd(aIDSZ8,{'001024' , 2952 })
    aadd(aIDSZ8,{'001025' , 2953 })
    aadd(aIDSZ8,{'001026' , 2954 })
    aadd(aIDSZ8,{'001028' , 2955 })
    aadd(aIDSZ8,{'001029' , 2956 })
    aadd(aIDSZ8,{'001030' , 2958 })
    aadd(aIDSZ8,{'001032' , 2959 })
    aadd(aIDSZ8,{'001033' , 2960 })
    aadd(aIDSZ8,{'001034' , 2962 })
    aadd(aIDSZ8,{'001035' , 2963 })
    aadd(aIDSZ8,{'001038' , 2981 })
    aadd(aIDSZ8,{'001039' , 2982 })
    aadd(aIDSZ8,{'001040' , 2983 })
    aadd(aIDSZ8,{'001041' , 2984 })
    aadd(aIDSZ8,{'001042' , 2985 })
    aadd(aIDSZ8,{'001043' , 2986 })
    aadd(aIDSZ8,{'001044' , 2987 })
    aadd(aIDSZ8,{'001045' , 2988 })
    aadd(aIDSZ8,{'001046' , 2989 })
    aadd(aIDSZ8,{'001047' , 2990 })
    aadd(aIDSZ8,{'001048' , 2991 })
    aadd(aIDSZ8,{'001049' , 2992 })
    aadd(aIDSZ8,{'001050' , 2993 })
    aadd(aIDSZ8,{'001051' , 2994 })
    aadd(aIDSZ8,{'001052' , 2995 })
    aadd(aIDSZ8,{'001053' , 2996 })
    aadd(aIDSZ8,{'001054' , 2997 })
    aadd(aIDSZ8,{'001055' , 2998 })
    aadd(aIDSZ8,{'001056' , 2999 })
    aadd(aIDSZ8,{'001057' , 3000 })
    aadd(aIDSZ8,{'001058' , 3001 })
    aadd(aIDSZ8,{'001059' , 3002 })
    aadd(aIDSZ8,{'001060' , 3003 })
    aadd(aIDSZ8,{'001061' , 3004 })
    aadd(aIDSZ8,{'001062' , 3005 })
    aadd(aIDSZ8,{'001063' , 3006 })
    aadd(aIDSZ8,{'001064' , 3007 })
    aadd(aIDSZ8,{'001065' , 3008 })
    aadd(aIDSZ8,{'001066' , 3009 })
    aadd(aIDSZ8,{'001067' , 3010 })
    aadd(aIDSZ8,{'001068' , 3011 })
    aadd(aIDSZ8,{'001069' , 3012 })
    aadd(aIDSZ8,{'001070' , 3013 })
    aadd(aIDSZ8,{'001071' , 3014 })
    aadd(aIDSZ8,{'001072' , 3015 })
    aadd(aIDSZ8,{'001073' , 3016 })
    aadd(aIDSZ8,{'001074' , 3017 })
    aadd(aIDSZ8,{'001075' , 3018 })
    aadd(aIDSZ8,{'001076' , 3019 })
    aadd(aIDSZ8,{'001077' , 3020 })
    aadd(aIDSZ8,{'001097' , 3055 })
    aadd(aIDSZ8,{'001098' , 3056 })
    aadd(aIDSZ8,{'001099' , 3057 })
    aadd(aIDSZ8,{'001100' , 3058 })
    aadd(aIDSZ8,{'001101' , 3059 })
    aadd(aIDSZ8,{'001102' , 3060 })
    aadd(aIDSZ8,{'001103' , 3061 })
    aadd(aIDSZ8,{'001104' , 3062 })
    aadd(aIDSZ8,{'001105' , 3063 })
    aadd(aIDSZ8,{'001106' , 3064 })
    aadd(aIDSZ8,{'001107' , 3065 })
    aadd(aIDSZ8,{'001108' , 3066 })
    aadd(aIDSZ8,{'001109' , 3067 })
    aadd(aIDSZ8,{'001110' , 3068 })
    aadd(aIDSZ8,{'001111' , 3069 })
    aadd(aIDSZ8,{'001112' , 3070 })
    aadd(aIDSZ8,{'001113' , 3071 })
    aadd(aIDSZ8,{'001114' , 3072 })
    aadd(aIDSZ8,{'001115' , 3073 })
    aadd(aIDSZ8,{'001116' , 3074 })
    aadd(aIDSZ8,{'001117' , 3075 })
    aadd(aIDSZ8,{'001118' , 3076 })
    aadd(aIDSZ8,{'001119' , 3077 })
    aadd(aIDSZ8,{'001120' , 3078 })
    aadd(aIDSZ8,{'001121' , 3079 })
    aadd(aIDSZ8,{'001122' , 3080 })
    aadd(aIDSZ8,{'001123' , 3081 })
    aadd(aIDSZ8,{'001124' , 3082 })
    aadd(aIDSZ8,{'001125' , 3083 })
    aadd(aIDSZ8,{'001126' , 3084 })
    aadd(aIDSZ8,{'001127' , 3085 })
    aadd(aIDSZ8,{'001128' , 3086 })
    aadd(aIDSZ8,{'001129' , 3087 })
    aadd(aIDSZ8,{'001130' , 3088 })
    aadd(aIDSZ8,{'001131' , 3089 })
    aadd(aIDSZ8,{'001132' , 3090 })
    aadd(aIDSZ8,{'001133' , 3091 })
    aadd(aIDSZ8,{'001135' , 3092 })
    aadd(aIDSZ8,{'001136' , 3093 })
    aadd(aIDSZ8,{'001137' , 3094 })
    aadd(aIDSZ8,{'001138' , 3095 })
    aadd(aIDSZ8,{'001140' , 3097 })
    aadd(aIDSZ8,{'001141' , 3098 })
    aadd(aIDSZ8,{'001143' , 3099 })
    aadd(aIDSZ8,{'001144' , 3100 })
    aadd(aIDSZ8,{'001145' , 3101 })
    aadd(aIDSZ8,{'001146' , 3102 })
    aadd(aIDSZ8,{'001147' , 3103 })
    aadd(aIDSZ8,{'001148' , 3104 })
    aadd(aIDSZ8,{'001149' , 3105 })
    aadd(aIDSZ8,{'001150' , 3106 })
    aadd(aIDSZ8,{'001151' , 3107 })
    aadd(aIDSZ8,{'001152' , 3108 })
    aadd(aIDSZ8,{'001153' , 3109 })
    aadd(aIDSZ8,{'001154' , 3110 })
    aadd(aIDSZ8,{'001155' , 3111 })
    aadd(aIDSZ8,{'001159' , 3117 })
    aadd(aIDSZ8,{'001160' , 3119 })
    aadd(aIDSZ8,{'001161' , 3120 })
    aadd(aIDSZ8,{'001162' , 3121 })
    aadd(aIDSZ8,{'001163' , 3122 })
    aadd(aIDSZ8,{'001164' , 3123 })
    aadd(aIDSZ8,{'001166' , 3124 })
    aadd(aIDSZ8,{'001167' , 3125 })
    aadd(aIDSZ8,{'001168' , 3126 })
    aadd(aIDSZ8,{'001169' , 3128 })
    aadd(aIDSZ8,{'001170' , 3129 })
    aadd(aIDSZ8,{'001171' , 3130 })
    aadd(aIDSZ8,{'001172' , 3131 })
    aadd(aIDSZ8,{'001173' , 3132 })
    aadd(aIDSZ8,{'001174' , 3133 })
    aadd(aIDSZ8,{'001175' , 3134 })
    aadd(aIDSZ8,{'001176' , 3135 })
    aadd(aIDSZ8,{'001177' , 3136 })
    aadd(aIDSZ8,{'001178' , 3137 })
    aadd(aIDSZ8,{'001179' , 3138 })
    aadd(aIDSZ8,{'001180' , 3139 })
    aadd(aIDSZ8,{'001181' , 3140 })
    aadd(aIDSZ8,{'001182' , 3141 })
    aadd(aIDSZ8,{'001183' , 3142 })
    aadd(aIDSZ8,{'001184' , 3143 })
    aadd(aIDSZ8,{'001185' , 3144 })
    aadd(aIDSZ8,{'001186' , 3145 })
    aadd(aIDSZ8,{'001188' , 3146 })
    aadd(aIDSZ8,{'001189' , 3147 })
    aadd(aIDSZ8,{'001190' , 3148 })
    aadd(aIDSZ8,{'001191' , 3149 })
    aadd(aIDSZ8,{'001192' , 3150 })
    aadd(aIDSZ8,{'001193' , 3151 })
    aadd(aIDSZ8,{'001194' , 3152 })
    aadd(aIDSZ8,{'001195' , 3153 })
    aadd(aIDSZ8,{'001196' , 3154 })
    aadd(aIDSZ8,{'001197' , 3155 })
    aadd(aIDSZ8,{'001198' , 3156 })
    aadd(aIDSZ8,{'001200' , 3157 })
    aadd(aIDSZ8,{'001201' , 3158 })
    aadd(aIDSZ8,{'001202' , 3159 })
    aadd(aIDSZ8,{'001206' , 3161 })
    aadd(aIDSZ8,{'001207' , 3162 })
    aadd(aIDSZ8,{'001208' , 3163 })
    aadd(aIDSZ8,{'001209' , 3164 })
    aadd(aIDSZ8,{'001210' , 3165 })
    aadd(aIDSZ8,{'001211' , 3166 })
    aadd(aIDSZ8,{'001212' , 3167 })
    aadd(aIDSZ8,{'001213' , 3168 })
    aadd(aIDSZ8,{'001214' , 3169 })
    aadd(aIDSZ8,{'001215' , 3170 })
    aadd(aIDSZ8,{'001216' , 3171 })
    aadd(aIDSZ8,{'001217' , 3172 })
    aadd(aIDSZ8,{'001218' , 3173 })
    aadd(aIDSZ8,{'001219' , 3174 })
    aadd(aIDSZ8,{'001220' , 3175 })
    aadd(aIDSZ8,{'001222' , 3176 })
    aadd(aIDSZ8,{'001223' , 3177 })
    aadd(aIDSZ8,{'001224' , 3178 })
    aadd(aIDSZ8,{'001225' , 3179 })
    aadd(aIDSZ8,{'001226' , 3180 })
    aadd(aIDSZ8,{'001227' , 3181 })
    aadd(aIDSZ8,{'001228' , 3183 })
    aadd(aIDSZ8,{'001255' , 3213 })
    aadd(aIDSZ8,{'001256' , 3214 })
    aadd(aIDSZ8,{'001258' , 3215 })
    aadd(aIDSZ8,{'001259' , 3216 })
    aadd(aIDSZ8,{'001260' , 3217 })
    aadd(aIDSZ8,{'001262' , 3220 })
    aadd(aIDSZ8,{'001263' , 3221 })
    aadd(aIDSZ8,{'001264' , 3222 })
    aadd(aIDSZ8,{'001265' , 3223 })
    aadd(aIDSZ8,{'001267' , 3225 })
    aadd(aIDSZ8,{'001270' , 3227 })
    aadd(aIDSZ8,{'001271' , 3228 })
    aadd(aIDSZ8,{'001272' , 3229 })
    aadd(aIDSZ8,{'001273' , 3230 })
    aadd(aIDSZ8,{'001274' , 3231 })
    aadd(aIDSZ8,{'001275' , 3232 })
    aadd(aIDSZ8,{'001276' , 3233 })
    aadd(aIDSZ8,{'001277' , 3234 })
    aadd(aIDSZ8,{'001278' , 3235 })
    aadd(aIDSZ8,{'001279' , 3236 })
    aadd(aIDSZ8,{'001280' , 3237 })
    aadd(aIDSZ8,{'001281' , 3238 })
    aadd(aIDSZ8,{'001282' , 3239 })
    aadd(aIDSZ8,{'001283' , 3240 })
    aadd(aIDSZ8,{'001284' , 3241 })
    aadd(aIDSZ8,{'001285' , 3242 })
    aadd(aIDSZ8,{'001286' , 3243 })
    aadd(aIDSZ8,{'001287' , 3244 })
    aadd(aIDSZ8,{'001288' , 3245 })
    aadd(aIDSZ8,{'001289' , 3246 })
    aadd(aIDSZ8,{'001290' , 3247 })
    aadd(aIDSZ8,{'001291' , 3248 })
    aadd(aIDSZ8,{'001292' , 3249 })
    aadd(aIDSZ8,{'001293' , 3250 })
    aadd(aIDSZ8,{'001294' , 3251 })
    aadd(aIDSZ8,{'001295' , 3252 })
    aadd(aIDSZ8,{'001296' , 3253 })
    aadd(aIDSZ8,{'001297' , 3254 })
    aadd(aIDSZ8,{'001298' , 3256 })
    aadd(aIDSZ8,{'001302' , 3259 })
    aadd(aIDSZ8,{'001304' , 3261 })
    aadd(aIDSZ8,{'001305' , 3262 })
    aadd(aIDSZ8,{'001306' , 3263 })
    aadd(aIDSZ8,{'001307' , 3264 })
    aadd(aIDSZ8,{'001308' , 3265 })
    aadd(aIDSZ8,{'001309' , 3266 })
    aadd(aIDSZ8,{'001310' , 3268 })
    aadd(aIDSZ8,{'001312' , 3269 })
    aadd(aIDSZ8,{'001313' , 3270 })
    aadd(aIDSZ8,{'001314' , 3271 })
    aadd(aIDSZ8,{'001315' , 3272 })
    aadd(aIDSZ8,{'001316' , 3273 })
    aadd(aIDSZ8,{'001317' , 3274 })
    aadd(aIDSZ8,{'001437' , 3695 })
    aadd(aIDSZ8,{'001459' , 3719 })
    aadd(aIDSZ8,{'001576' , 3903 })
    aadd(aIDSZ8,{'001582' , 3923 })
    aadd(aIDSZ8,{'001598' , 3998 })
    For n1 := 1 to Len(aIDSZ8)

        lAuto := .t.
        //nOper    :=  iif(empty(aRetPro[n1][3]), 3,4) //// 3 - Inclusao, 4 - Alteração, 5 - Exclusão
        //nOper    :=  3 //iif(empty(aRetPro[n1][3]), 3,4) //// 3 - Inclusao, 4 - Alteração, 5 - Exclusão
        nOper    :=  4 //iif(empty(aRetPro[n1][3]), 3,4) //// 3 - Inclusao, 4 - Alteração, 5 - Exclusão
        //   cPrdProc :=  aRetPro[n1][1]
        //   cIDSZ7   :=  iif(!empty(aRetPro[n1][2]),aRetPro[n1][2],cIDSZ7)

        //   FWMsgRun( ,{|| fProc(cTabVen,nOper,cPrdProc,cIDSZ7,aRetPro[n1][3])}," Processando Produto "+cPrdProc+"...")
        FWMsgRun( ,{|| fProc2(nOper,aIDSZ8[n1])}," Processando ")

    Next n1


    //EEcView(cMsg, "Itens Não Processados")
    //  if len(aLogProc) > 0
    //      cMsg := ""
    //      cEol := chr(10)
    //      For n1 := 1 to Len(aLogProc)
    //          cMsg +=trim( aLogProc[n1][1])+" | "+trim( aLogProc[n1][2])+" | "+trim( aLogProc[n1][3]) + cEol
    //      Next n1
    //      EEcView(cMsg, "Itens Não Processados")
    //  endif

    /*Retorna o conteudo do MV_PARXX*/


    RestArea(aArea)
Return



Static Function fProc2(nOper,aIDSZ8)
    DBSELECTAREA("SZ9")
    SZ9->(dbSetOrder(1))

    DBSELECTAREA("SZ8")
    SZ8->(dbSetOrder(1))

    SZ8->(dbGoTo(aIDSZ8[2]))
    conout("stop")
    oModel := FWLoadModel("DLP02F02")
    oModel:SetOperation(nOper)
    oModel:Activate()


    cDesc :=  PADR("GERADO VIA ROTINA AUTOMATICA",GETSX3CACHE("Z8_DESC","X3_TAMANHO")      )
    oMDSZ8Cab := oModel:GetModel("SZ8MASTER")
    oMDSZ901 := oModel:GetModel("SZ9DETAIL01")
    oMDSZ902 := oModel:GetModel("SZ9DETAIL02")
    oMDSZ903 := oModel:GetModel("SZ9DETAIL03")

    CONOUT("STOP")
    // oModel:SetOperation(MODEL_OPERATION_INSERT)
    // oSZ8Cab:Activate()
    // oSZ901:Activate()
    // oSZ902:Activate()
    // oSZ903:Activate()

    //IF   oMDSZ8Cab:GetValue("Z8_COD") !=  cPrdProc
    //    conout("teste")
    //ENDIF
    //if nOper != 4
    //    oMDSZ8Cab:SetValue("Z8_IDSZ7"    , cIDSZ7      )
    //endif
    //oMDSZ8Cab:SetValue("Z8_COD"      , cPrdProc      )
    //oMDSZ8Cab:SetValue("Z8_DESC"     ,cDesc )
    oMDSZ8Cab:SetValue("Z8_FATMP"  , 3.1      )

    CONOUT("STOP")
    U_D02fPDados()
    CONOUT("STOP")
    //  Z8_IDSZ7 000002
    //  Z8_COD 90262780
    //  Z8_DSCPRD CHICOTE DE LIGACAO
    //  Z8_CDTABVN 109
    lOk := .T.

    If oModel:VldData()
        If oModel:CommitData()
            lOk := .T.

            //Se não deu certo, altera a variável para false
        Else
            lOk := .F.
        EndIf

        //Se não conseguir validar as informações, altera a variável para false
    Else
        lOk := .F.
    EndIf

    If ! lOk
        //Busca o Erro do Modelo de Dados
        aErro := oModel:GetErrorMessage()

        //Monta o Texto que será mostrado na tela
        cMessage := "Id do formulário de origem:"  + ' [' + cValToChar(aErro[01]) + '], '
        cMessage += "Id do campo de origem: "      + ' [' + cValToChar(aErro[02]) + '], '
        cMessage += "Id do formulário de erro: "   + ' [' + cValToChar(aErro[03]) + '], '
        cMessage += "Id do campo de erro: "        + ' [' + cValToChar(aErro[04]) + '], '
        cMessage += "Id do erro: "                 + ' [' + cValToChar(aErro[05]) + '], '
        cMessage += "Mensagem do erro: "           + ' [' + cValToChar(aErro[06]) + '], '
        cMessage += "Mensagem da solução: "        + ' [' + cValToChar(aErro[07]) + '], '
        cMessage += "Valor atribuído: "            + ' [' + cValToChar(aErro[08]) + '], '
        cMessage += "Valor anterior: "             + ' [' + cValToChar(aErro[09]) + ']'

        //Mostra mensagem de erro
        //   lRet := .F.
        ConOut("Erro: " + cMessage)
        // Else
        //     //  lRet := .T.
        //     ConOut("Produto incluido!")
    EndIf
    //Desativa o modelo de dados
    oModel:DeActivate()
Return

/*/{Protheus.doc} fGetProd
REtorna os Produtos elegiveis se é necessario incluir ou alterar
@author Gabriel
@since 09/12/2021
@param cTabVen,cProdDe,cProdAte,cIDSZ7,cAtual
@return return_var, return_type, return_description
/*/
static Function fGetProd(cTabVen,cProdDe,cProdAte,cIDSZ7,cAtual,aRetPro)
    Local aRet := {}
    Local cEol := chr(10)

    /*
" + retsqlname("") + " SB1 (NOLOCK) " + cEol
    */
    cSql := " SELECT DISTINCT SBZ.BZ_FILIAL, B1_COD, B1_DESC, SBZ.BZ_YIDSZ7, ISNULL('', SPACE(6)) Z8_ID, ISNULL(SZ8.Z8_IDSZ7, SPACE(6)) Z8_IDSZ7 " + cEol
    cSql += "   FROM dbo." + retsqlname("SB1") + " SB1  (NOLOCK) "      + cEol
    cSql += "       JOIN dbo." + retsqlname("SBZ") + " SBZ (NOLOCK) "   + cEol
    cSql += "             ON  SBZ.D_E_L_E_T_  = '' "                    + cEol
    cSql += "             AND SBZ.BZ_FILIAL   = "+VALTOSQL(XFILIAL("SBZ"))                + cEol
    cSql += "             AND SB1.B1_COD      = SBZ.BZ_COD  "           + cEol
    cSql += "       JOIN dbo." + retsqlname("DA1") + " DA1 (NOLOCK) "   + cEol
    cSql += "             ON  DA1.D_E_L_E_T_  = '' AND DA1_ATIVO = '1' "           + cEol
    cSql += "             AND DA1.DA1_FILIAL   = "+VALTOSQL(XFILIAL("DA1"))        + cEol
    cSql += "             AND SB1.B1_COD      = DA1.DA1_CODPRO  "           + cEol
    cSql += "             AND DA1.DA1_CODTAB   = "+VALTOSQL(cTabVen)                + cEol
    cSql += "       LEFT JOIN " + retsqlname("SZ8") + " SZ8 (NOLOCK) "  + cEol
    cSql += "             ON  SZ8.D_E_L_E_T_ = ''"                      + cEol
    cSql += "             AND SZ8.Z8_FILIAL  = "+VALTOSQL(XFILIAL("SZ8"))                      + cEol
    cSql += "             AND SB1.B1_COD     = SZ8.Z8_COD"              + cEol
    cSql += " WHERE SB1.D_E_L_E_T_ = ''"   + cEol
    cSql += "       AND SB1.B1_COD BETWEEN  " + VALTOSQL(cProdDe) + "  AND  " + VALTOSQL(cProdAte) + "  "  + cEol
    cSql += "AND SB1.B1_MSBLQL != '1'"  + cEol
    cSql += "ORDER BY 1,2 "

    If Select('TMPSB1') <> 0
        TMPSB1->(dbCloseArea())
    Endif

    CONOUT("TESTE")
    TCQuery cSql Alias TMPSB1 New
    While TMPSB1->(!eof())

        aTmp :={}

        aadd(aTmp,TMPSB1->B1_COD       ) /*01 - PRODUTO*/
        aadd(aTmp,TMPSB1->BZ_YIDSZ7    ) /*02 - BZ_YIDSZ7*/
        aadd(aTmp,TMPSB1->Z8_ID        ) /*03 - Z8_ID*/

        aadd(aRet,aTmp)
        TMPSB1->(dbskip())

    Enddo
    aRetPro := aRet
    TMPSB1->(dbCloseArea())
Return



Static Function fProc(cTabVen,nOper,cPrdProc,cIDSZ7,cIDSZ8)
    DBSELECTAREA("SZ9")
    SZ9->(dbSetOrder(1))
    if nOPer == 3
        cDesc :=  PADR("INSERT AUTOMATICO",GETSX3CACHE("Z8_DESC","X3_TAMANHO")      )
    ELSE
        cDesc :=  PADR("UPDATE AUTOMATICO",GETSX3CACHE("Z8_DESC","X3_TAMANHO")      )

        DBSELECTAREA("SZ8")
        SZ8->(dbSetOrder(1))
        SZ8->(MsSeek(xFilial("SZ8")+cIDSZ8))


    ENDIF
    conout("stop")
    oModel := FWLoadModel("DLP02F02")
    oModel:SetOperation(nOper)
    oModel:Activate()


    cDesc :=  PADR("GERADO VIA ROTINA AUTOMATICA",GETSX3CACHE("Z8_DESC","X3_TAMANHO")      )
    oMDSZ8Cab := oModel:GetModel("SZ8MASTER")
    oMDSZ901 := oModel:GetModel("SZ9DETAIL01")
    oMDSZ902 := oModel:GetModel("SZ9DETAIL02")
    oMDSZ903 := oModel:GetModel("SZ9DETAIL03")

    CONOUT("STOP")
    // oModel:SetOperation(MODEL_OPERATION_INSERT)
    // oSZ8Cab:Activate()
    // oSZ901:Activate()
    // oSZ902:Activate()
    // oSZ903:Activate()

    IF   oMDSZ8Cab:GetValue("Z8_COD") !=  cPrdProc
        conout("teste")
    ENDIF
    if nOper != 4
        oMDSZ8Cab:SetValue("Z8_IDSZ7"    , cIDSZ7      )
    endif
    oMDSZ8Cab:SetValue("Z8_COD"      , cPrdProc      )
    oMDSZ8Cab:SetValue("Z8_DESC"     ,cDesc )
    oMDSZ8Cab:SetValue("Z8_CDTABVN"  , cTabVen      )

    CONOUT("STOP")
    U_D02fPDados()
    CONOUT("STOP")
    //  Z8_IDSZ7 000002
    //  Z8_COD 90262780
    //  Z8_DSCPRD CHICOTE DE LIGACAO
    //  Z8_CDTABVN 109
    lOk := .T.

    If oModel:VldData()
        If oModel:CommitData()
            lOk := .T.

            //Se não deu certo, altera a variável para false
        Else
            lOk := .F.
        EndIf

        //Se não conseguir validar as informações, altera a variável para false
    Else
        lOk := .F.
    EndIf

    If ! lOk
        //Busca o Erro do Modelo de Dados
        aErro := oModel:GetErrorMessage()

        //Monta o Texto que será mostrado na tela
        cMessage := "Id do formulário de origem:"  + ' [' + cValToChar(aErro[01]) + '], '
        cMessage += "Id do campo de origem: "      + ' [' + cValToChar(aErro[02]) + '], '
        cMessage += "Id do formulário de erro: "   + ' [' + cValToChar(aErro[03]) + '], '
        cMessage += "Id do campo de erro: "        + ' [' + cValToChar(aErro[04]) + '], '
        cMessage += "Id do erro: "                 + ' [' + cValToChar(aErro[05]) + '], '
        cMessage += "Mensagem do erro: "           + ' [' + cValToChar(aErro[06]) + '], '
        cMessage += "Mensagem da solução: "        + ' [' + cValToChar(aErro[07]) + '], '
        cMessage += "Valor atribuído: "            + ' [' + cValToChar(aErro[08]) + '], '
        cMessage += "Valor anterior: "             + ' [' + cValToChar(aErro[09]) + ']'

        //Mostra mensagem de erro
        //   lRet := .F.
        ConOut("Erro: " + cMessage)
        // Else
        //     //  lRet := .T.
        //     ConOut("Produto incluido!")
    EndIf
    //Desativa o modelo de dados
    oModel:DeActivate()
Return

/*//Pegando o modelo de dados, setando a operação de inclusão
oModel := FWLoadModel("MATA010")
oModel:SetOperation(3)
oModel:Activate()

//Pegando o model e setando os campos
oSB1Mod := oModel:GetModel("SB1MASTER")
oSB1Mod:SetValue("B1_COD"    , cCod      )
oSB1Mod:SetValue("B1_DESC"   , cDesc     )
oSB1Mod:SetValue("B1_TIPO"   , cTipo     )
oSB1Mod:SetValue("B1_UM"     , cUM       )
oSB1Mod:SetValue("B1_LOCPAD" , cLocPad   )

//Setando o complemento do produto
oSB5Mod := oModel:GetModel("SB5DETAIL")
If oSB5Mod != Nil
    oSB5Mod:SetValue("B5_CEME"   , cCEME     )
EndIf

//Se conseguir validar as informações
If oModel:VldData()

    //Tenta realizar o Commit
    If oModel:CommitData()
        lOk := .T.

    //Se não deu certo, altera a variável para false
    Else
        lOk := .F.
    EndIf

//Se não conseguir validar as informações, altera a variável para false
Else
    lOk := .F.
EndIf

//Se não deu certo a inclusão, mostra a mensagem de erro
If ! lOk
    //Busca o Erro do Modelo de Dados
    aErro := oModel:GetErrorMessage()

    //Monta o Texto que será mostrado na tela
    cMessage := "Id do formulário de origem:"  + ' [' + cValToChar(aErro[01]) + '], '
    cMessage += "Id do campo de origem: "      + ' [' + cValToChar(aErro[02]) + '], '
    cMessage += "Id do formulário de erro: "   + ' [' + cValToChar(aErro[03]) + '], '
    cMessage += "Id do campo de erro: "        + ' [' + cValToChar(aErro[04]) + '], '
    cMessage += "Id do erro: "                 + ' [' + cValToChar(aErro[05]) + '], '
    cMessage += "Mensagem do erro: "           + ' [' + cValToChar(aErro[06]) + '], '
    cMessage += "Mensagem da solução: "        + ' [' + cValToChar(aErro[07]) + '], '
    cMessage += "Valor atribuído: "            + ' [' + cValToChar(aErro[08]) + '], '
    cMessage += "Valor anterior: "             + ' [' + cValToChar(aErro[09]) + ']'

    //Mostra mensagem de erro
    lRet := .F.
    ConOut("Erro: " + cMessage)
Else
    lRet := .T.
    ConOut("Produto incluido!")
EndIf

//Desativa o modelo de dados
oModel:DeActivate()*/
