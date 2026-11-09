package br.ime.finflow.assinaturas.dto;

import java.time.LocalDate;
import java.util.List;

/** Resposta de POST /assinaturas/lancamentos. */
public record ResultadoLancamento(
        int mes,
        int ano,
        List<ItemLancado> lancadas,
        int jaLancadasAntes) {

    public record ItemLancado(Integer idAssinatura, String nome, Integer idTransacao, LocalDate data, Long valor) {
    }
}
