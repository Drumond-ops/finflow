package br.ime.finflow.assinaturas.dto;

import br.ime.finflow.assinaturas.dominio.Assinatura;
import br.ime.finflow.assinaturas.dominio.Periodicidade;
import java.time.LocalDate;

/** O que a API devolve para cada assinatura (JSON em snake_case). */
public record AssinaturaResponse(
        Integer id,
        String nome,
        Long valor,
        Periodicidade periodicidade,
        LocalDate dataInicio,
        Boolean ativa,
        Integer idCartao,
        Integer idCategoria,
        long custoMensal,
        long custoAnual,
        LocalDate proximaCobranca) {

    public static AssinaturaResponse de(Assinatura a, LocalDate proximaCobranca) {
        return new AssinaturaResponse(
                a.getId(), a.getNome(), a.getValor(), a.getPeriodicidade(), a.getDataInicio(), a.getAtiva(),
                a.getIdCartao(), a.getIdCategoria(), a.custoMensal(), a.custoAnual(), proximaCobranca);
    }
}
