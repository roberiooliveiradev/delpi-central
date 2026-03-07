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
                    Cadastro Corporativo
                </div>

                <h1 class="login-energy-title">
                    Criar Conta
                </h1>
            </div>
        </div>

        <form id="kc-register-form"
              action="${url.registrationAction}"
              method="post">

            <input type="text" name="firstName" placeholder="Nome" />
            <input type="text" name="lastName" placeholder="Sobrenome" />
            <input type="email" name="email" placeholder="Email" />
            <input type="text" name="username" placeholder="Usuário" />
            <input type="password" name="password" placeholder="Senha" />
            <input type="password" name="password-confirm" placeholder="Confirmar senha" />

            <button class="login-energy-action" type="submit">
                Criar conta
            </button>

        </form>

    </div>
</div>

<script src="${url.resourcesPath}/js/lightning.js"></script>

</#if>

</@layout.registrationLayout>