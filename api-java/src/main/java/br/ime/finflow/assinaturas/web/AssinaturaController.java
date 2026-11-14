package br.ime.finflow.assinaturas.web;

import br.ime.finflow.assinaturas.dto.AssinaturaRequest;
import br.ime.finflow.assinaturas.dto.AssinaturaResponse;
import br.ime.finflow.assinaturas.dto.ResultadoLancamento;
import br.ime.finflow.assinaturas.dto.ResumoAssinaturas;
import br.ime.finflow.assinaturas.seguranca.AutenticacaoInterceptor;
import br.ime.finflow.assinaturas.servico.AssinaturaService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestAttribute;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

/**
 * Rotas REST de assinaturas. O id do usuário vem do token (colocado na requisição
 * pelo AutenticacaoInterceptor), nunca do corpo da requisição.
 */
@RestController
@RequestMapping("/assinaturas")
@Tag(name = "Assinaturas")
@SecurityRequirement(name = "bearerAuth")
public class AssinaturaController {

    private static final String USUARIO = AutenticacaoInterceptor.ATRIBUTO_ID_USUARIO;

    private final AssinaturaService servico;

    public AssinaturaController(AssinaturaService servico) {
        this.servico = servico;
    }

    // ---------- CREATE ----------

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "Cadastrar assinatura")
    public AssinaturaResponse criar(@Valid @RequestBody AssinaturaRequest dados,
                                    @RequestAttribute(USUARIO) Integer idUsuario) {
        return servico.criar(dados, idUsuario);
    }

    // ---------- RETRIEVE ----------

    @GetMapping
    @Operation(summary = "Listar minhas assinaturas")
    public List<AssinaturaResponse> listar(@RequestAttribute(USUARIO) Integer idUsuario) {
        return servico.listar(idUsuario);
    }

    @GetMapping("/resumo")
    @Operation(summary = "Custo mensal/anual das assinaturas ativas e próximas cobranças")
    public ResumoAssinaturas resumo(@RequestParam(defaultValue = "30") int dias,
                                    @RequestAttribute(USUARIO) Integer idUsuario) {
        return servico.resumo(idUsuario, dias);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Ler uma assinatura")
    public AssinaturaResponse buscar(@PathVariable Integer id, @RequestAttribute(USUARIO) Integer idUsuario) {
        return servico.buscar(id, idUsuario);
    }

    // ---------- UPDATE ----------

    @PutMapping("/{id}")
    @Operation(summary = "Editar assinatura (inclusive pausar com \"ativa\": false)")
    public AssinaturaResponse atualizar(@PathVariable Integer id, @Valid @RequestBody AssinaturaRequest dados,
                                        @RequestAttribute(USUARIO) Integer idUsuario) {
        return servico.atualizar(id, dados, idUsuario);
    }

    // ---------- DELETE ----------

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Apagar assinatura")
    public void apagar(@PathVariable Integer id, @RequestAttribute(USUARIO) Integer idUsuario) {
        servico.apagar(id, idUsuario);
    }

    // ---------- INTEGRAÇÃO COM AS TRANSAÇÕES ----------

    @PostMapping("/lancamentos")
    @Operation(summary = "Lançar as cobranças do mês como despesas (aparecem na fatura e no dashboard)")
    public ResultadoLancamento lancar(@RequestParam int mes, @RequestParam int ano,
                                      @RequestAttribute(USUARIO) Integer idUsuario) {
        return servico.lancarCobrancas(idUsuario, mes, ano);
    }
}
