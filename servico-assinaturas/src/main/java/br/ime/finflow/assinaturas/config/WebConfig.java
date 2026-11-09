package br.ime.finflow.assinaturas.config;

import br.ime.finflow.assinaturas.seguranca.AutenticacaoInterceptor;
import java.util.Arrays;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    private final AutenticacaoInterceptor autenticacao;
    private final String[] origensPermitidas;

    public WebConfig(AutenticacaoInterceptor autenticacao, @Value("${finflow.cors-origins}") String origens) {
        this.autenticacao = autenticacao;
        this.origensPermitidas = Arrays.stream(origens.split(","))
                .map(String::trim)
                .filter(origem -> !origem.isEmpty())
                .toArray(String[]::new);
    }

    /** Exige login em todas as rotas de assinaturas (o Swagger e o /status ficam livres). */
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(autenticacao).addPathPatterns("/assinaturas", "/assinaturas/**");
    }

    /** Libera o frontend (que roda em outro endereço) para chamar esta API pelo navegador. */
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**")
                .allowedOrigins(origensPermitidas)
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
                .allowedHeaders("*")
                .allowCredentials(true);
    }
}
