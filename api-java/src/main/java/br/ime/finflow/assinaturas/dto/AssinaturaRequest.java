package br.ime.finflow.assinaturas.dto;

import br.ime.finflow.assinaturas.dominio.Periodicidade;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;

/**
 * Corpo do POST e do PUT de /assinaturas (o "schema" de entrada, como no Pydantic).
 * Em JSON os campos vêm em snake_case: data_inicio, id_cartao, id_categoria.
 */
public class AssinaturaRequest {

    @NotBlank(message = "o nome é obrigatório")
    @Size(max = 60, message = "o nome pode ter no máximo 60 caracteres")
    private String nome;

    @NotNull(message = "o valor é obrigatório")
    @Positive(message = "o valor deve ser maior que zero (em centavos)")
    private Long valor;

    @NotNull(message = "a periodicidade é obrigatória (MENSAL ou ANUAL)")
    private Periodicidade periodicidade;

    @NotNull(message = "a data de início é obrigatória")
    private LocalDate dataInicio;

    /** Opcional: cartão onde a assinatura é cobrada. Sem cartão, é débito/pix. */
    private Integer idCartao;

    /** Opcional: se vazio, usa a categoria "Assinaturas" do usuário. */
    private Integer idCategoria;

    /** Opcional: padrão true. Assinatura pausada (false) não entra no resumo nem nos lançamentos. */
    private Boolean ativa;

    public String getNome() { return nome; }
    public void setNome(String nome) { this.nome = nome; }

    public Long getValor() { return valor; }
    public void setValor(Long valor) { this.valor = valor; }

    public Periodicidade getPeriodicidade() { return periodicidade; }
    public void setPeriodicidade(Periodicidade periodicidade) { this.periodicidade = periodicidade; }

    public LocalDate getDataInicio() { return dataInicio; }
    public void setDataInicio(LocalDate dataInicio) { this.dataInicio = dataInicio; }

    public Integer getIdCartao() { return idCartao; }
    public void setIdCartao(Integer idCartao) { this.idCartao = idCartao; }

    public Integer getIdCategoria() { return idCategoria; }
    public void setIdCategoria(Integer idCategoria) { this.idCategoria = idCategoria; }

    public Boolean getAtiva() { return ativa; }
    public void setAtiva(Boolean ativa) { this.ativa = ativa; }
}
