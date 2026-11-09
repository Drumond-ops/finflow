package br.ime.finflow.assinaturas.seguranca;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.nio.charset.StandardCharsets;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

/**
 * Roda ANTES de toda rota de /assinaturas: lê o cabeçalho "Authorization: Bearer <token>",
 * valida o token e guarda o id do usuário na requisição (atributo "idUsuario").
 * É o equivalente ao get_usuario_atual da API em Python.
 */
@Component
public class AutenticacaoInterceptor implements HandlerInterceptor {

    public static final String ATRIBUTO_ID_USUARIO = "idUsuario";

    private final JwtService jwtService;
    private final JdbcTemplate jdbc;

    public AutenticacaoInterceptor(JwtService jwtService, JdbcTemplate jdbc) {
        this.jwtService = jwtService;
        this.jdbc = jdbc;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler)
            throws Exception {
        // O navegador manda um OPTIONS antes (CORS "preflight") sem token: deixamos passar
        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            return true;
        }

        String cabecalho = request.getHeader("Authorization");
        if (cabecalho == null || !cabecalho.startsWith("Bearer ")) {
            return negar(response);
        }

        int idUsuario;
        try {
            idUsuario = jwtService.validarEObterIdUsuario(cabecalho.substring("Bearer ".length()).trim());
        } catch (JwtService.TokenInvalidoException e) {
            return negar(response);
        }

        // Token válido, mas o usuário pode ter apagado a conta
        Integer existe = jdbc.queryForObject("SELECT COUNT(*) FROM usuarios WHERE id = ?", Integer.class, idUsuario);
        if (existe == null || existe == 0) {
            return negar(response);
        }

        request.setAttribute(ATRIBUTO_ID_USUARIO, idUsuario);
        return true;
    }

    private boolean negar(HttpServletResponse response) throws Exception {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setHeader("WWW-Authenticate", "Bearer");
        response.setContentType("application/json");
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());
        response.getWriter().write("{\"detail\": \"Token inválido ou expirado. Faça login novamente.\"}");
        return false; // não chega no controller
    }
}
