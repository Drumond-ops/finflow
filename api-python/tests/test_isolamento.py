"""O teste mais importante de segurança: um usuário nunca enxerga nem mexe nos dados de outro."""
from conftest import id_categoria


def test_usuario_nao_ve_nem_altera_dados_de_outro(cliente, ana, bruno):
    cat_ana = id_categoria(cliente, ana)
    cartao_ana = cliente.post("/cartoes/", headers=ana, json={"nome": "Nubank"}).json()["id"]
    trans_ana = cliente.post(
        "/transacoes/", headers=ana,
        json={"tipo": "despesa", "valor": 5000, "data": "2026-10-05", "id_categoria": cat_ana},
    ).json()["id"]
    obj_ana = cliente.post("/objetivos/", headers=ana, json={"nome": "Viagem", "valor_alvo": 1000}).json()["id"]
    aporte_ana = cliente.post(
        "/aportes/", headers=ana, json={"valor": 100, "data": "2026-10-01", "id_objetivo": obj_ana}
    ).json()["id"]
    plan_ana = cliente.post(
        "/planejamentos/", headers=ana,
        json={"mes": 10, "ano": 2026, "valor": 1000, "id_cartao": cartao_ana, "id_categoria": cat_ana},
    ).json()["id"]

    # Listagens do Bruno não trazem nada da Ana
    assert cliente.get("/transacoes/", headers=bruno).json() == []
    assert cliente.get("/cartoes/", headers=bruno).json() == []
    assert cliente.get("/objetivos/", headers=bruno).json() == []
    assert cliente.get("/aportes/", headers=bruno).json() == []
    assert cliente.get("/planejamentos/", headers=bruno).json() == []
    assert cat_ana not in [c["id"] for c in cliente.get("/categorias/", headers=bruno).json()]

    # Ler, editar ou apagar pelo id: sempre 404
    for rota in [f"/transacoes/{trans_ana}", f"/cartoes/{cartao_ana}", f"/categorias/{cat_ana}",
                 f"/objetivos/{obj_ana}", f"/aportes/{aporte_ana}", f"/planejamentos/{plan_ana}"]:
        assert cliente.get(rota, headers=bruno).status_code == 404, rota
        assert cliente.delete(rota, headers=bruno).status_code == 404, rota

    assert cliente.get(f"/cartoes/{cartao_ana}/fatura/?mes=10&ano=2026", headers=bruno).status_code == 404

    # Bruno também não consegue usar a categoria/cartão/objetivo da Ana nos lançamentos dele
    cat_bruno = id_categoria(cliente, bruno)
    r = cliente.post("/transacoes/", headers=bruno,
                     json={"tipo": "despesa", "valor": 1, "data": "2026-10-05", "id_categoria": cat_ana})
    assert r.status_code == 404
    r = cliente.post("/transacoes/", headers=bruno,
                     json={"tipo": "despesa", "valor": 1, "data": "2026-10-05",
                           "id_categoria": cat_bruno, "id_cartao": cartao_ana})
    assert r.status_code == 404
    r = cliente.post("/aportes/", headers=bruno, json={"valor": 1, "data": "2026-10-01", "id_objetivo": obj_ana})
    assert r.status_code == 404

    # E os dados da Ana continuam intactos
    assert cliente.get(f"/transacoes/{trans_ana}", headers=ana).status_code == 200
