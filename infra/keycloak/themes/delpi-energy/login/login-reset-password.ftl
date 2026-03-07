<#import "template.ftl" as layout>
<@layout.registrationLayout displayInfo=false; section>

<#if section == "form">

<div class="login-energy">
    <svg class="lightning-svg"></svg>

    <div class="login-energy-card">

        <div class="login-energy-brand">
            <div class="login-energy-logo">
                <img src="${url.resourcesPath}/img/logoMinhaDelpi.svg" />
            </div>

            <div class="login-energy-brand-text">
                <div class="login-energy-kicker">
                    Recuperação de Acesso
                </div>

                <h1 class="login-energy-title">
                    Redefinir Senha
                </h1>

                <p class="login-energy-subtitle">
                    Informe seu usuário ou email para receber instruções.
                </p>
            </div>
        </div>

        <form id="kc-reset-password-form"
              action="${url.loginAction}"
              method="post">

            <#if message?has_content>
                <div class="kc-feedback">
                    ${kcSanitize(message.summary)?no_esc}
                </div>
            </#if>

            <input type="text"
                   name="username"
                   value="${(auth.attemptedUsername!'')}"
                   placeholder="Usuário ou email"
                   autofocus />

            <button class="login-energy-action" type="submit">
                Enviar instruções
            </button>

        </form>

        <div class="login-energy-footer">
            Link temporário • Validade limitada
        </div>

    </div>
</div>

<script src="${url.resourcesPath}/js/lightning.js"></script>

</#if>

</@layout.registrationLayout>