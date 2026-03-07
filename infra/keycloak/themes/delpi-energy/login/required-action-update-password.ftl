<#import "template.ftl" as layout>
<@layout.registrationLayout displayInfo=false; section>

<#if section = "header">
    Atualizar Senha

<#elseif section = "form">

<div class="login-energy">
    <svg class="lightning-svg"></svg>

    <div class="login-energy-card">

        <div class="login-energy-brand">
            <div class="login-energy-logo">
                <img src="${url.resourcesPath}/img/logoMinhaDelpi.svg" />
            </div>

            <div class="login-energy-brand-text">
                <div class="login-energy-kicker">
                    Segurança de Conta
                </div>

                <h1 class="login-energy-title">
                    Atualizar Senha
                </h1>

                <p class="login-energy-subtitle">
                    Para ativar sua conta, defina uma nova senha segura.
                </p>
            </div>
        </div>

        <form id="kc-passwd-update-form"
              action="${url.loginAction}"
              method="post">

            <#if message?has_content>
                <div class="kc-feedback">
                    ${kcSanitize(message.summary)?no_esc}
                </div>
            </#if>

            <input type="password"
                   name="password-new"
                   placeholder="Nova senha"
                   autofocus />

            <input type="password"
                   name="password-confirm"
                   placeholder="Confirmar nova senha" />

            <#if logoutOtherSessions??>
                <label style="display:flex;gap:8px;margin:12px 0;">
                    <input type="checkbox"
                           name="logout-sessions"
                           value="on"
                           checked />
                    Encerrar sessões ativas
                </label>
            </#if>

            <button class="login-energy-action" type="submit">
                Atualizar senha
            </button>

        </form>

        <div class="login-energy-footer">
            Segurança reforçada • Criptografia ativa
        </div>

    </div>
</div>

<script src="${url.resourcesPath}/js/lightning.js"></script>

</#if>

</@layout.registrationLayout>