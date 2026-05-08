<#macro registrationLayout bodyClass="" displayInfo=false displayMessage=true displayRequiredFields=false>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8" />

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0, viewport-fit=cover" />

    <meta name="robots" content="noindex, nofollow" />
    <meta name="color-scheme" content="light dark" />

    <link
        rel="icon"
        type="image/svg+xml"
        href="${url.resourcesPath}/img/logoMinhaDelpi.svg" />

    <title>Minha DELPI</title>

    <#if properties.stylesCommon?has_content>
        <#list properties.stylesCommon?split(' ') as style>
            <link
                href="${url.resourcesCommonPath}/${style}"
                rel="stylesheet" />
        </#list>
    </#if>

    <#if properties.styles?has_content>
        <#list properties.styles?split(' ') as style>
            <link
                href="${url.resourcesPath}/${style}"
                rel="stylesheet" />
        </#list>
    </#if>
</head>

<body class="login-pf ${bodyClass}">

    <#nested "form">

    <#if displayInfo>
        <#nested "info">
    </#if>

</body>
</html>
</#macro>