package br.ime.finflow.assinaturas.dto;

import java.time.LocalDate;
import java.util.List;

/** Resposta de GET /assinaturas/resumo. Valores em centavos. */
public record ResumoAssinaturas(
        int quantidadeAtivas,
        long custoMensal,
        long custoAnual,
        List<ProximaCobranca> proximasCobrancas) {

    public record ProximaCobranca(Integer idAssinatura, String nome, Long valor, LocalDate data, Integer idCartao) {
    }
}
