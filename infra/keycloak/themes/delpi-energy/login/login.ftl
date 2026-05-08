<#import "template.ftl" as layout>
<@layout.registrationLayout displayInfo=false; section>

<#if section = "header">
    Minha DELPI

<#elseif section = "form">

<div class="login-energy">

    <svg class="lightning-svg"></svg>

    <div class="login-energy-card">

        <div class="login-energy-brand">
            <div class="login-energy-logo">
                <img 
                alt="Minha DELPI"
                src="${url.resourcesPath}/img/logoMinhaDelpi.svg" />
            </div>

            <div class="login-energy-brand-text">
                <div class="login-energy-kicker">
                    <svg xmlns="http://www.w3.org/2000/svg" 
                    width="16" height="16" viewBox="0 0 24 24" 
                    fill="none" stroke="currentColor" stroke-width="2"
                    stroke-linecap="round" 
                    stroke-linejoin="round" class="lucide lucide-activity" 
                    aria-hidden="true">
                    <path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"></path></svg>
                    Faça login para acessar a plataforma
                </div>
            </div>
        </div>

        <form id="kc-form-login"
              class="login-energy-form"
              action="${url.loginAction}"
              method="post">

            <#if message?has_content>
                <div class="kc-feedback">
                    ${kcSanitize(message.summary)?no_esc}
                </div>
            </#if>

            <input type="text"
                   name="username"
                   value="${(login.username!'')}"
                   placeholder="Usuário ou email"
                   autocomplete="username"
                   autofocus />

            <input type="password"
                   name="password"
                   placeholder="Senha"
                   autocomplete="current-password"
                   data-password-toggle="true" />

            <label class="login-energy-password-toggle">
                <input type="checkbox"
                       class="js-toggle-passwords" />
                <span>Mostrar senha</span>
            </label>

            <input type="hidden"
                   name="credentialId"
                   <#if auth.selectedCredential?has_content>
                       value="${auth.selectedCredential}"
                   </#if> />

            <button class="login-energy-action"
                    type="submit"
                    name="login">
                Entrar
            </button>

        </form>

        <p class="login-energy-subtitle">
            Plataforma corporativa de governança, aplicações e integrações.
        </p>

    </div>
</div>

<script src="${url.resourcesPath}/js/lightning.js"></script>
<script src="${url.resourcesPath}/js/password-toggle.js"></script>

</#if>

</@layout.registrationLayout>