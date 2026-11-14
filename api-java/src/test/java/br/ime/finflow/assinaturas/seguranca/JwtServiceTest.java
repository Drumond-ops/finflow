package br.ime.finflow.assinaturas.seguranca;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import org.junit.jupiter.api.Test;

class JwtServiceTest {

    private static final String CHAVE = "chave-de-desenvolvimento-troque-em-producao";

    /**
     * Token gerado de verdade pela API em Python (PyJWT) com a chave acima:
     * {"sub": "7", "iat": 09/11/2026 12:00 UTC, "exp": 10/11/2026 12:00 UTC}
     */
    private static final String TOKEN_DO_PYTHON =
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
                    + "eyJzdWIiOiI3IiwiaWF0IjoxNzk0MjI1NjAwLCJleHAiOjE3OTQzMTIwMDB9."
                    + "m-22n-m3v_V3swfPSfNk5gymv3Fmv9m81nfXwrne-ag";

    private static JwtService servicoEm(String instanteUtc) {
        return new JwtService(CHAVE, Clock.fixed(Instant.parse(instanteUtc), ZoneOffset.UTC));
    }

    @Test
    void aceitaTokenGeradoPelaApiPython() {
        assertThat(servicoEm("2026-11-09T15:00:00Z").validarEObterIdUsuario(TOKEN_DO_PYTHON)).isEqualTo(7);
    }

    @Test
    void recusaTokenExpirado() {
        assertThatThrownBy(() -> servicoEm("2026-11-11T00:00:00Z").validarEObterIdUsuario(TOKEN_DO_PYTHON))
                .isInstanceOf(JwtService.TokenInvalidoException.class);
    }

    @Test
    void recusaTokenComOutraChave() {
        JwtService outraChave = new JwtService("outra-chave-qualquer-com-tamanho-suficiente",
                Clock.fixed(Instant.parse("2026-11-09T15:00:00Z"), ZoneOffset.UTC));
        assertThatThrownBy(() -> outraChave.validarEObterIdUsuario(TOKEN_DO_PYTHON))
                .isInstanceOf(JwtService.TokenInvalidoException.class);
    }

    @Test
    void recusaTokenAdulterado() {
        // Troca o conteúdo para {"sub":"8",...} mantendo a assinatura antiga
        String[] partes = TOKEN_DO_PYTHON.split("\\.");
        String conteudoFalso = java.util.Base64.getUrlEncoder().withoutPadding()
                .encodeToString("{\"sub\":\"8\",\"exp\":1794312000}".getBytes());
        String adulterado = partes[0] + "." + conteudoFalso + "." + partes[2];

        assertThatThrownBy(() -> servicoEm("2026-11-09T15:00:00Z").validarEObterIdUsuario(adulterado))
                .isInstanceOf(JwtService.TokenInvalidoException.class);
    }

    @Test
    void recusaLixo() {
        JwtService servico = servicoEm("2026-11-09T15:00:00Z");
        assertThatThrownBy(() -> servico.validarEObterIdUsuario("abc")).isInstanceOf(JwtService.TokenInvalidoException.class);
        assertThatThrownBy(() -> servico.validarEObterIdUsuario("a.b.c")).isInstanceOf(JwtService.TokenInvalidoException.class);
        assertThatThrownBy(() -> servico.validarEObterIdUsuario(null)).isInstanceOf(JwtService.TokenInvalidoException.class);
    }
}
