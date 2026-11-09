package br.ime.finflow.assinaturas.dominio;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/**
 * Tabela "assinatura_lancamentos": anota que a cobrança de uma assinatura num mês
 * já virou uma transação. Assim, lançar o mesmo mês duas vezes não duplica nada.
 */
@Entity
@Table(name = "assinatura_lancamentos")
public class LancamentoAssinatura {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false)
    private Integer mes;

    @Column(nullable = false)
    private Integer ano;

    @Column(name = "id_assinatura", nullable = false)
    private Integer idAssinatura;

    @Column(name = "id_transacao", nullable = false)
    private Integer idTransacao;

    protected LancamentoAssinatura() {
        // exigido pelo JPA
    }

    public LancamentoAssinatura(Integer idAssinatura, Integer mes, Integer ano, Integer idTransacao) {
        this.idAssinatura = idAssinatura;
        this.mes = mes;
        this.ano = ano;
        this.idTransacao = idTransacao;
    }

    public Integer getId() { return id; }
    public Integer getMes() { return mes; }
    public Integer getAno() { return ano; }
    public Integer getIdAssinatura() { return idAssinatura; }
    public Integer getIdTransacao() { return idTransacao; }
}
