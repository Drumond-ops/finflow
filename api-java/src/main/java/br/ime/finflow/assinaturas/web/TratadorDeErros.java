package br.ime.finflow.assinaturas.web;

import java.util.Map;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.ErrorResponse;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.server.ResponseStatusException;

/**
 * Transforma exceções em respostas JSON no MESMO formato da API Python: {"detail": "..."}.
 * Assim o frontend trata os erros das duas APIs do mesmo jeito.
 */
@RestControllerAdvice
public class TratadorDeErros {

    private static final Logger log = LoggerFactory.getLogger(TratadorDeErros.class);

    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<Map<String, Object>> erroComStatus(ResponseStatusException e) {
        return ResponseEntity.status(e.getStatusCode()).body(Map.of("detail", String.valueOf(e.getReason())));
    }

    /** Falha nas validações do AssinaturaRequest (@NotBlank, @Positive...). */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> dadosInvalidos(MethodArgumentNotValidException e) {
        String mensagens = e.getBindingResult().getFieldErrors().stream()
                .map(erro -> erro.getDefaultMessage())
                .collect(Collectors.joining("; "));
        return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY).body(Map.of("detail", mensagens));
    }

    /** JSON malformado, data em formato errado, periodicidade diferente de MENSAL/ANUAL... */
    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<Map<String, Object>> jsonInvalido(HttpMessageNotReadableException e) {
        return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY).body(Map.of(
                "detail", "JSON inválido. Confira os campos: datas no formato AAAA-MM-DD e periodicidade MENSAL ou ANUAL."));
    }

    @ExceptionHandler({MissingServletRequestParameterException.class, MethodArgumentTypeMismatchException.class})
    public ResponseEntity<Map<String, Object>> parametroInvalido(Exception e) {
        return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY).body(Map.of("detail", e.getMessage()));
    }

    /** Ex.: duas requisições ao mesmo tempo tentando lançar a mesma cobrança. */
    @ExceptionHandler(DataIntegrityViolationException.class)
    public ResponseEntity<Map<String, Object>> conflito(DataIntegrityViolationException e) {
        return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of(
                "detail", "A operação conflita com dados já existentes. Atualize a página e tente de novo."));
    }

    /**
     * Qualquer outro erro: a API responde em JSON e continua no ar.
     * Erros "conhecidos" do Spring (rota inexistente = 404, método errado = 405...) mantêm o status certo.
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> erroGenerico(Exception e) {
        if (e instanceof ErrorResponse erroDoSpring) {
            String detalhe = erroDoSpring.getBody().getDetail();
            return ResponseEntity.status(erroDoSpring.getStatusCode())
                    .body(Map.of("detail", detalhe != null ? detalhe : "Requisição inválida"));
        }
        log.error("Erro inesperado", e);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("detail", "Erro interno no servidor. Tente novamente."));
    }
}
