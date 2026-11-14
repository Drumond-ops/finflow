package br.ime.finflow.assinaturas.dominio;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDate;

/** Tabela "assinaturas" (criada pela API em Python, ver models.py). */
@Entity
@Table(name = "assinaturas")
public class Assinatura {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false, length = 60)
    private String nome;

    /** Valor em centavos (R$ 39,90 = 3990), igual ao resto do projeto. */
    @Column(nullable = false)
    private Long valor;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 10)
    private Periodicidade periodicidade;

    /** Data da primeira cobrança. Define o dia (e, se anual, o mês) das próximas. */
    @Column(name = "data_inicio", nullable = false)
    private LocalDate dataInicio;

    @Column(nullable = false)
    private Boolean ativa;

    @Column(name = "id_usuario", nullable = false)
    private Integer idUsuario;

    @Column(name = "id_cartao")
    private Integer idCartao;

    @Column(name = "id_categoria")
    private Integer idCategoria;

    /** Custo equivalente por mês (anual dividido por 12), em centavos. */
    public long custoMensal() {
        return periodicidade == Periodicidade.ANUAL ? Math.round(valor / 12.0) : valor;
    }

    /** Custo total em 12 meses, em centavos. */
    public long custoAnual() {
        return periodicidade == Periodicidade.ANUAL ? valor : valor * 12;
    }

    // ---------- getters e setters ----------

    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }

    public String getNome() { return nome; }
    public void setNome(String nome) { this.nome = nome; }

    public Long getValor() { return valor; }
    public void setValor(Long valor) { this.valor = valor; }

    public Periodicidade getPeriodicidade() { return periodicidade; }
    public void setPeriodicidade(Periodicidade periodicidade) { this.periodicidade = periodicidade; }

    public LocalDate getDataInicio() { return dataInicio; }
    public void setDataInicio(LocalDate dataInicio) { this.dataInicio = dataInicio; }

    public Boolean getAtiva() { return ativa; }
    public void setAtiva(Boolean ativa) { this.ativa = ativa; }

    public Integer getIdUsuario() { return idUsuario; }
    public void setIdUsuario(Integer idUsuario) { this.idUsuario = idUsuario; }

    public Integer getIdCartao() { return idCartao; }
    public void setIdCartao(Integer idCartao) { this.idCartao = idCartao; }

    public Integer getIdCategoria() { return idCategoria; }
    public void setIdCategoria(Integer idCategoria) { this.idCategoria = idCategoria; }
}
