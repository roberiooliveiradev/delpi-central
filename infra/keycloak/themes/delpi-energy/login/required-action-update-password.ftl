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
                <img src="${url.resourcesPath}/img/logoMinhaDelpi.svg"
                     alt="Minha DELPI" />
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
              class="login-energy-form"
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
                   autocomplete="new-password"
                   data-password-toggle="true"
                   autofocus />

            <input type="password"
                   name="password-confirm"
                   placeholder="Confirmar nova senha"
                   autocomplete="new-password"
                   data-password-toggle="true" />

            <label class="login-energy-password-toggle">
                <input type="checkbox"
                       class="js-toggle-passwords" />
                <span>Mostrar senha</span>
            </label>

            <#if logoutOtherSessions??>
                <label class="login-energy-checkbox">
                    <input type="checkbox"
                           name="logout-sessions"
                           value="on"
                           checked />
                    <span>Encerrar sessões ativas</span>
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
<script src="${url.resourcesPath}/js/password-toggle.js"></script>

</#if>

</@layout.registrationLayout>