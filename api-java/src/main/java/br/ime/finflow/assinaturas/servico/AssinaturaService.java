package br.ime.finflow.assinaturas.servico;

import br.ime.finflow.assinaturas.dominio.Assinatura;
import br.ime.finflow.assinaturas.dominio.LancamentoAssinatura;
import br.ime.finflow.assinaturas.dto.AssinaturaRequest;
import br.ime.finflow.assinaturas.dto.AssinaturaResponse;
import br.ime.finflow.assinaturas.dto.ResultadoLancamento;
import br.ime.finflow.assinaturas.dto.ResultadoLancamento.ItemLancado;
import br.ime.finflow.assinaturas.dto.ResumoAssinaturas;
import br.ime.finflow.assinaturas.dto.ResumoAssinaturas.ProximaCobranca;
import br.ime.finflow.assinaturas.repositorio.AssinaturaRepository;
import br.ime.finflow.assinaturas.repositorio.LancamentoAssinaturaRepository;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

/**
 * Regras de negócio das assinaturas.
 *
 * Usa JPA (repositórios) para as tabelas de assinaturas e JdbcTemplate (SQL direto) para
 * conversar com as tabelas da API Python: cartoes, categorias e transacoes.
 */
@Service
public class AssinaturaService {

    private static final ZoneId FUSO = ZoneId.of("America/Sao_Paulo");
    private static final String NOME_CATEGORIA_PADRAO = "Assinaturas";

    private final AssinaturaRepository assinaturas;
    private final LancamentoAssinaturaRepository lancamentos;
    private final JdbcTemplate jdbc;

    public AssinaturaService(AssinaturaRepository assinaturas, LancamentoAssinaturaRepository lancamentos,
                             JdbcTemplate jdbc) {
        this.assinaturas = assinaturas;
        this.lancamentos = lancamentos;
        this.jdbc = jdbc;
    }

    // ==========================
    // CRUD
    // ==========================

    public List<AssinaturaResponse> listar(int idUsuario) {
        LocalDate hoje = hoje();
        return assinaturas.findByIdUsuarioOrderByNomeAsc(idUsuario).stream()
                .map(a -> paraResposta(a, hoje))
                .toList();
    }

    public AssinaturaResponse buscar(int id, int idUsuario) {
        return paraResposta(buscarDoUsuario(id, idUsuario), hoje());
    }

    @Transactional
    public AssinaturaResponse criar(AssinaturaRequest dados, int idUsuario) {
        validarVinculos(dados, idUsuario);
        Assinatura nova = new Assinatura();
        nova.setIdUsuario(idUsuario);
        copiarCampos(dados, nova);
        return paraResposta(assinaturas.save(nova), hoje());
    }

    @Transactional
    public AssinaturaResponse atualizar(int id, AssinaturaRequest dados, int idUsuario) {
        Assinatura existente = buscarDoUsuario(id, idUsuario);
        validarVinculos(dados, idUsuario);
        copiarCampos(dados, existente);
        return paraResposta(assinaturas.save(existente), hoje());
    }

    /** Apaga a assinatura. As transações que ela já gerou continuam no extrato (o dinheiro saiu). */
    @Transactional
    public void apagar(int id, int idUsuario) {
        assinaturas.delete(buscarDoUsuario(id, idUsuario));
    }

    // ==========================
    // RESUMO
    // ==========================

    public ResumoAssinaturas resumo(int idUsuario, int dias) {
        if (dias < 1 || dias > 366) {
            throw new ResponseStatusException(HttpStatus.UNPROCESSABLE_ENTITY, "dias deve estar entre 1 e 366");
        }
        LocalDate hoje = hoje();
        LocalDate limite = hoje.plusDays(dias);
        List<Assinatura> ativas = assinaturas.findByIdUsuarioAndAtivaTrueOrderByNomeAsc(idUsuario);

        List<ProximaCobranca> proximas = new ArrayList<>();
        for (Assinatura a : ativas) {
            for (LocalDate data : CalendarioCobranca.cobrancasEntre(a.getPeriodicidade(), a.getDataInicio(), hoje, limite)) {
                proximas.add(new ProximaCobranca(a.getId(), a.getNome(), a.getValor(), data, a.getIdCartao()));
            }
        }
        proximas.sort(Comparator.comparing(ProximaCobranca::data).thenComparing(ProximaCobranca::nome));

        long custoMensal = ativas.stream().mapToLong(Assinatura::custoMensal).sum();
        long custoAnual = ativas.stream().mapToLong(Assinatura::custoAnual).sum();
        return new ResumoAssinaturas(ativas.size(), custoMensal, custoAnual, proximas);
    }

    // ==========================
    // LANÇAR COBRANÇAS COMO TRANSAÇÕES
    // ==========================

    /**
     * Para cada assinatura ativa com cobrança no mês, cria a DESPESA na tabela de transações
     * (no cartão da assinatura, se tiver). Assim ela aparece na fatura, no dashboard e no
     * orçamento da API Python. Rodar duas vezes para o mesmo mês não duplica nada.
     */
    @Transactional
    public ResultadoLancamento lancarCobrancas(int idUsuario, int mes, int ano) {
        if (mes < 1 || mes > 12 || ano < 2000 || ano > 2100) {
            throw new ResponseStatusException(HttpStatus.UNPROCESSABLE_ENTITY, "mes deve ser de 1 a 12 e ano de 2000 a 2100");
        }

        List<ItemLancado> lancadas = new ArrayList<>();
        int jaLancadas = 0;

        for (Assinatura a : assinaturas.findByIdUsuarioAndAtivaTrueOrderByNomeAsc(idUsuario)) {
            Optional<LocalDate> data = CalendarioCobranca.cobrancaNoMes(a.getPeriodicidade(), a.getDataInicio(), mes, ano);
            if (data.isEmpty()) {
                continue;
            }
            if (lancamentos.existsByIdAssinaturaAndMesAndAno(a.getId(), mes, ano)) {
                jaLancadas++;
                continue;
            }

            int idCategoria = a.getIdCategoria() != null ? a.getIdCategoria() : categoriaPadrao(idUsuario);
            String descricao = ("Assinatura: " + a.getNome());
            if (descricao.length() > 100) {
                descricao = descricao.substring(0, 100);
            }

            Integer idTransacao = jdbc.queryForObject(
                    "INSERT INTO transacoes (tipo, valor, data, descricao, id_usuario, id_cartao, id_categoria) "
                            + "VALUES ('despesa', ?, ?, ?, ?, ?, ?) RETURNING id",
                    Integer.class,
                    a.getValor(), data.get(), descricao, idUsuario, a.getIdCartao(), idCategoria);

            lancamentos.save(new LancamentoAssinatura(a.getId(), mes, ano, idTransacao));
            lancadas.add(new ItemLancado(a.getId(), a.getNome(), idTransacao, data.get(), a.getValor()));
        }

        return new ResultadoLancamento(mes, ano, lancadas, jaLancadas);
    }

    // ==========================
    // AUXILIARES
    // ==========================

    private Assinatura buscarDoUsuario(int id, int idUsuario) {
        // Se não existe OU é de outro usuário: 404 nos dois casos (não revela que o id existe)
        return assinaturas.findByIdAndIdUsuario(id, idUsuario)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Assinatura não encontrada"));
    }

    private void validarVinculos(AssinaturaRequest dados, int idUsuario) {
        if (dados.getIdCartao() != null && !pertenceAoUsuario("cartoes", dados.getIdCartao(), idUsuario)) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Cartão não encontrado(a)");
        }
        if (dados.getIdCategoria() != null && !pertenceAoUsuario("categorias", dados.getIdCategoria(), idUsuario)) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Categoria não encontrado(a)");
        }
    }

    /** tabela vem sempre do nosso código ("cartoes" ou "categorias"), nunca do usuário. */
    private boolean pertenceAoUsuario(String tabela, int id, int idUsuario) {
        Integer total = jdbc.queryForObject(
                "SELECT COUNT(*) FROM " + tabela + " WHERE id = ? AND id_usuario = ?", Integer.class, id, idUsuario);
        return total != null && total > 0;
    }

    /** Categoria "Assinaturas" do usuário (criada no registro). Se ele apagou, cria de novo. */
    private int categoriaPadrao(int idUsuario) {
        List<Integer> ids = jdbc.queryForList(
                "SELECT id FROM categorias WHERE id_usuario = ? AND LOWER(nome) = LOWER(?) ORDER BY id LIMIT 1",
                Integer.class, idUsuario, NOME_CATEGORIA_PADRAO);
        if (!ids.isEmpty()) {
            return ids.get(0);
        }
        return jdbc.queryForObject(
                "INSERT INTO categorias (nome, id_usuario) VALUES (?, ?) RETURNING id",
                Integer.class, NOME_CATEGORIA_PADRAO, idUsuario);
    }

    private static void copiarCampos(AssinaturaRequest dados, Assinatura destino) {
        destino.setNome(dados.getNome().trim());
        destino.setValor(dados.getValor());
        destino.setPeriodicidade(dados.getPeriodicidade());
        destino.setDataInicio(dados.getDataInicio());
        destino.setIdCartao(dados.getIdCartao());
        destino.setIdCategoria(dados.getIdCategoria());
        destino.setAtiva(dados.getAtiva() == null || dados.getAtiva());
    }

    private static AssinaturaResponse paraResposta(Assinatura a, LocalDate hoje) {
        LocalDate proxima = Boolean.TRUE.equals(a.getAtiva())
                ? CalendarioCobranca.proximaCobranca(a.getPeriodicidade(), a.getDataInicio(), hoje).orElse(null)
                : null;
        return AssinaturaResponse.de(a, proxima);
    }

    private static LocalDate hoje() {
        return LocalDate.now(FUSO);
    }
}
