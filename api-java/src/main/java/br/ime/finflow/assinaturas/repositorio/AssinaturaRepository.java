package br.ime.finflow.assinaturas.repositorio;

import br.ime.finflow.assinaturas.dominio.Assinatura;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

/**
 * O Spring Data gera o SQL sozinho a partir do NOME do método.
 * Ex.: findByIdAndIdUsuario -> SELECT ... WHERE id = ? AND id_usuario = ?
 */
public interface AssinaturaRepository extends JpaRepository<Assinatura, Integer> {

    List<Assinatura> findByIdUsuarioOrderByNomeAsc(Integer idUsuario);

    List<Assinatura> findByIdUsuarioAndAtivaTrueOrderByNomeAsc(Integer idUsuario);

    Optional<Assinatura> findByIdAndIdUsuario(Integer id, Integer idUsuario);
}
