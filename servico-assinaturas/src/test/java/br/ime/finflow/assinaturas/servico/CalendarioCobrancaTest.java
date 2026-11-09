package br.ime.finflow.assinaturas.servico;

import static br.ime.finflow.assinaturas.dominio.Periodicidade.ANUAL;
import static br.ime.finflow.assinaturas.dominio.Periodicidade.MENSAL;
import static org.assertj.core.api.Assertions.assertThat;

import java.time.LocalDate;
import org.junit.jupiter.api.Test;

class CalendarioCobrancaTest {

    private static LocalDate d(String iso) {
        return LocalDate.parse(iso);
    }

    @Test
    void mensalCobraTodoMesNoMesmoDia() {
        assertThat(CalendarioCobranca.cobrancaNoMes(MENSAL, d("2026-01-15"), 11, 2026)).contains(d("2026-11-15"));
    }

    @Test
    void dia31EmFevereiroViraUltimoDiaDoMes() {
        assertThat(CalendarioCobranca.cobrancaNoMes(MENSAL, d("2026-01-31"), 2, 2026)).contains(d("2026-02-28"));
        assertThat(CalendarioCobranca.cobrancaNoMes(MENSAL, d("2026-01-31"), 2, 2028)).contains(d("2028-02-29"));
    }

    @Test
    void naoCobraAntesDaDataDeInicio() {
        assertThat(CalendarioCobranca.cobrancaNoMes(MENSAL, d("2026-11-10"), 10, 2026)).isEmpty();
    }

    @Test
    void anualSoCobraNoMesDeAniversario() {
        assertThat(CalendarioCobranca.cobrancaNoMes(ANUAL, d("2025-03-20"), 3, 2026)).contains(d("2026-03-20"));
        assertThat(CalendarioCobranca.cobrancaNoMes(ANUAL, d("2025-03-20"), 4, 2026)).isEmpty();
    }

    @Test
    void cobrancasEntreDatas() {
        assertThat(CalendarioCobranca.cobrancasEntre(MENSAL, d("2026-01-05"), d("2026-11-09"), d("2027-01-08")))
                .containsExactly(d("2026-12-05"), d("2027-01-05"));
    }

    @Test
    void proximaCobranca() {
        // Hoje é dia 9 e a cobrança é dia 5: a próxima é no mês seguinte
        assertThat(CalendarioCobranca.proximaCobranca(MENSAL, d("2026-01-05"), d("2026-11-09"))).contains(d("2026-12-05"));
        // Cobrança no próprio dia de hoje conta
        assertThat(CalendarioCobranca.proximaCobranca(MENSAL, d("2026-01-09"), d("2026-11-09"))).contains(d("2026-11-09"));
        // Assinatura que ainda vai começar
        assertThat(CalendarioCobranca.proximaCobranca(ANUAL, d("2027-02-01"), d("2026-11-09"))).contains(d("2027-02-01"));
    }
}
