package br.ime.finflow.assinaturas.servico;

import br.ime.finflow.assinaturas.dominio.Periodicidade;
import java.time.LocalDate;
import java.time.YearMonth;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * Regras de data das cobranças (sem banco de dados, fácil de testar).
 *
 * - MENSAL: cobra todo mês no dia da data de início. Dia 31 em fevereiro vira 28/29.
 * - ANUAL: cobra uma vez por ano, no mês e dia da data de início.
 * - Nada é cobrado antes da data de início.
 */
public final class CalendarioCobranca {

    private CalendarioCobranca() {
    }

    /** Data da cobrança no mês informado, ou vazio se não há cobrança nesse mês. */
    public static Optional<LocalDate> cobrancaNoMes(Periodicidade periodicidade, LocalDate dataInicio, int mes, int ano) {
        YearMonth alvo = YearMonth.of(ano, mes);
        YearMonth primeiroMes = YearMonth.from(dataInicio);

        if (alvo.isBefore(primeiroMes)) {
            return Optional.empty();
        }
        if (periodicidade == Periodicidade.ANUAL && alvo.getMonthValue() != dataInicio.getMonthValue()) {
            return Optional.empty();
        }

        int dia = Math.min(dataInicio.getDayOfMonth(), alvo.lengthOfMonth());
        return Optional.of(alvo.atDay(dia));
    }

    /** Todas as cobranças entre 'de' e 'ate' (inclusive), em ordem. */
    public static List<LocalDate> cobrancasEntre(Periodicidade periodicidade, LocalDate dataInicio, LocalDate de, LocalDate ate) {
        List<LocalDate> datas = new ArrayList<>();
        for (YearMonth mes = YearMonth.from(de); !mes.isAfter(YearMonth.from(ate)); mes = mes.plusMonths(1)) {
            cobrancaNoMes(periodicidade, dataInicio, mes.getMonthValue(), mes.getYear())
                    .filter(data -> !data.isBefore(de) && !data.isAfter(ate))
                    .ifPresent(datas::add);
        }
        return datas;
    }

    /** Próxima cobrança a partir de 'hoje' (inclusive). Procura até 13 meses à frente. */
    public static Optional<LocalDate> proximaCobranca(Periodicidade periodicidade, LocalDate dataInicio, LocalDate hoje) {
        LocalDate inicioBusca = hoje.isBefore(dataInicio) ? dataInicio : hoje;
        return cobrancasEntre(periodicidade, dataInicio, inicioBusca, inicioBusca.plusMonths(13)).stream().findFirst();
    }
}
