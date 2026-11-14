package br.ime.finflow.assinaturas.repositorio;

import br.ime.finflow.assinaturas.dominio.LancamentoAssinatura;
import org.springframework.data.jpa.repository.JpaRepository;

public interface LancamentoAssinaturaRepository extends JpaRepository<LancamentoAssinatura, Integer> {

    boolean existsByIdAssinaturaAndMesAndAno(Integer idAssinatura, Integer mes, Integer ano);
}
