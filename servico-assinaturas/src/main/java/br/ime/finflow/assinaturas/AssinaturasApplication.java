package br.ime.finflow.assinaturas;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.enums.SecuritySchemeType;
import io.swagger.v3.oas.annotations.info.Info;
import io.swagger.v3.oas.annotations.security.SecurityScheme;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Serviço de assinaturas do FinFlow, em Java com Spring Boot.
 *
 * Ele divide o banco com a API em Python e aceita o MESMO token de login:
 * o usuário entra pela API Python (POST /auth/login) e usa o token aqui também.
 */
@SpringBootApplication
@OpenAPIDefinition(info = @Info(
        title = "FinFlow - Assinaturas (Java)",
        version = "0.1.0",
        description = "Controle de assinaturas (Netflix, Spotify...). Faça login na API Python "
                + "(POST /auth/login em http://localhost:8000/docs), copie o access_token e cole em Authorize."))
@SecurityScheme(name = "bearerAuth", type = SecuritySchemeType.HTTP, scheme = "bearer", bearerFormat = "JWT")
public class AssinaturasApplication {

    public static void main(String[] args) {
        SpringApplication.run(AssinaturasApplication.class, args);
    }
}
