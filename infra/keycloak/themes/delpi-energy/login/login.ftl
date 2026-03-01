<#import "template.ftl" as layout>
<@layout.registrationLayout displayInfo=false; section>

<#if section == "form">

<div class="login-energy">

    <!-- SVG DINÂMICO -->
    <svg class="lightning-svg"></svg>

    <div class="login-energy-card">

        <div class="login-energy-brand">
            <div class="login-energy-logo">
                <img src="${url.resourcesPath}/img/logoDelpi.svg" />
            </div>

            <div class="login-energy-brand-text">
                <div class="login-energy-kicker">
                    ⚡ Energia & Conectividade
                </div>

                <h1 class="login-energy-title">
                    Central DELPI
                </h1>

                <p class="login-energy-subtitle">
                    Plataforma corporativa de governança, aplicações e integrações.
                </p>
            </div>
        </div>

        <form id="kc-form-login"
              action="${url.loginAction}"
              method="post">

            <#if message?has_content>
                <div class="kc-feedback">
                    ${kcSanitize(message.summary)?no_esc}
                </div>
            </#if>

            <input type="text"
                   id="username"
                   name="username"
                   value="${(login.username!'')}"
                   placeholder="Usuário ou email"
                   autofocus />

            <input type="password"
                   id="password"
                   name="password"
                   placeholder="Senha" />

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

        <div class="login-energy-footer">
            <div class="login-energy-dot"></div>
            Ambiente protegido • Tokens curtos • Refresh automático
        </div>

    </div>
</div>

<script src="${url.resourcesPath}/js/lightning.js"></script>

</#if>

</@layout.registrationLayout>