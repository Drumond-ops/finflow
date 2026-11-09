package br.ime.finflow.assinaturas.web;

import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class StatusController {

    /** Rota pública para saber se o serviço está no ar. */
    @GetMapping("/")
    public Map<String, String> status() {
        return Map.of("status", "ok", "servico", "assinaturas (Java)", "documentacao", "/swagger-ui.html");
    }
}
