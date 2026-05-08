<#import "template.ftl" as layout>
<@layout.registrationLayout displayInfo=false; section>

<#if section == "form">

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
                    Cadastro Corporativo
                </div>

                <h1 class="login-energy-title">
                    Criar Conta
                </h1>
            </div>
        </div>

        <form id="kc-register-form"
              class="login-energy-form"
              action="${url.registrationAction}"
              method="post">

            <#if message?has_content>
                <div class="kc-feedback">
                    ${kcSanitize(message.summary)?no_esc}
                </div>
            </#if>

            <input type="text"
                   name="firstName"
                   value="${(register.formData.firstName!'')}"
                   placeholder="Nome"
                   autocomplete="given-name" />

            <input type="text"
                   name="lastName"
                   value="${(register.formData.lastName!'')}"
                   placeholder="Sobrenome"
                   autocomplete="family-name" />

            <input type="email"
                   name="email"
                   value="${(register.formData.email!'')}"
                   placeholder="Email"
                   autocomplete="email" />

            <input type="text"
                   name="username"
                   value="${(register.formData.username!'')}"
                   placeholder="Usuário"
                   autocomplete="username" />

            <input type="password"
                   name="password"
                   placeholder="Senha"
                   autocomplete="new-password"
                   data-password-toggle="true" />

            <input type="password"
                   name="password-confirm"
                   placeholder="Confirmar senha"
                   autocomplete="new-password"
                   data-password-toggle="true" />

            <label class="login-energy-password-toggle">
                <input type="checkbox"
                       class="js-toggle-passwords" />
                <span>Mostrar senha</span>
            </label>

            <button class="login-energy-action" type="submit">
                Criar conta
            </button>

        </form>

    </div>
</div>

<script src="${url.resourcesPath}/js/lightning.js"></script>
<script src="${url.resourcesPath}/js/password-toggle.js"></script>

</#if>

</@layout.registrationLayout>