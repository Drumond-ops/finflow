package br.ime.finflow.assinaturas.seguranca;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Clock;
import java.util.Base64;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Confere os tokens JWT gerados pela API em Python (PyJWT, algoritmo HS256).
 *
 * Um JWT tem 3 partes separadas por ponto: cabecalho.conteudo.assinatura
 *   - cabecalho e conteudo são JSON em Base64URL
 *   - assinatura = HMAC-SHA256(cabecalho + "." + conteudo, SECRET_KEY)
 * Se alguém alterar o conteúdo (ex.: trocar o id do usuário), a assinatura não bate mais.
 */
@Component
public class JwtService {

    private final byte[] chave;
    private final ObjectMapper json = new ObjectMapper();
    private final Clock relogio;

    @Autowired
    public JwtService(@Value("${finflow.secret-key}") String secretKey) {
        this(secretKey, Clock.systemUTC());
    }

    /** Construtor usado nos testes, para controlar o "agora". */
    JwtService(String secretKey, Clock relogio) {
        this.chave = secretKey.getBytes(StandardCharsets.UTF_8);
        this.relogio = relogio;
    }

    /**
     * Valida o token e devolve o id do usuário (campo "sub").
     *
     * @throws TokenInvalidoException se o token estiver malformado, adulterado ou expirado
     */
    public int validarEObterIdUsuario(String token) {
        String[] partes = token == null ? new String[0] : token.split("\\.");
        if (partes.length != 3) {
            throw new TokenInvalidoException("Token malformado");
        }

        try {
            JsonNode cabecalho = json.readTree(decodificar(partes[0]));
            if (!"HS256".equals(cabecalho.path("alg").asText())) {
                throw new TokenInvalidoException("Algoritmo não suportado");
            }

            byte[] assinaturaEsperada = hmacSha256(partes[0] + "." + partes[1]);
            byte[] assinaturaRecebida = decodificar(partes[2]);
            // isEqual compara em tempo constante (não dá pista de quantos bytes acertou)
            if (!MessageDigest.isEqual(assinaturaEsperada, assinaturaRecebida)) {
                throw new TokenInvalidoException("Assinatura inválida");
            }

            JsonNode conteudo = json.readTree(decodificar(partes[1]));
            long expiraEm = conteudo.path("exp").asLong(0);
            if (expiraEm <= relogio.instant().getEpochSecond()) {
                throw new TokenInvalidoException("Token expirado");
            }

            return Integer.parseInt(conteudo.path("sub").asText());
        } catch (TokenInvalidoException e) {
            throw e;
        } catch (Exception e) { // Base64 inválido, JSON inválido, sub não numérico...
            throw new TokenInvalidoException("Token inválido");
        }
    }

    private byte[] hmacSha256(String dados) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(chave, "HmacSHA256"));
        return mac.doFinal(dados.getBytes(StandardCharsets.US_ASCII));
    }

    private static byte[] decodificar(String base64Url) {
        return Base64.getUrlDecoder().decode(base64Url);
    }

    public static class TokenInvalidoException extends RuntimeException {
        public TokenInvalidoException(String mensagem) {
            super(mensagem);
        }
    }
}
