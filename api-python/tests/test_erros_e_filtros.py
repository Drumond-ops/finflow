"""Requisitos do enunciado: respostas em JSON e erros tratados sem derrubar a API."""
from conftest import id_categoria


def test_erros_comuns_respondem_json(cliente, ana):
    r = cliente.get("/transacoes/999999", headers=ana)  # item não encontrado
    assert r.status_code == 404 and r.json()["detail"]

    r = cliente.post("/transacoes/", headers=ana, json={"tipo": "xpto", "valor": -1})  # dado inválido
    assert r.status_code == 422 and r.json()["detail"]

    r = cliente.get("/rota-que-nao-existe")
    assert r.status_code == 404 and r.json()["detail"]

    r = cliente.get("/categorias/")  # sem login
    assert r.status_code == 401 and r.json()["detail"]


def test_erro_inesperado_vira_500_em_json_e_a_api_continua_no_ar(cliente, ana, monkeypatch):
    import routers.categorias as rc

    def quebra(*args, **kwargs):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(rc, "_checar_nome_repetido", quebra)
    r = cliente.post("/categorias/", headers=ana, json={"nome": "Pets"})
    assert r.status_code == 500 and r.json()["detail"]
    assert cliente.get("/categorias/", headers=ana).status_code == 200


def test_filtro_por_periodo_e_origem(cliente, ana):
    mercado = id_categoria(cliente, ana, "Mercado")
    cartao = cliente.post("/cartoes/", headers=ana, json={"nome": "Nubank", "dia_fechamento": 3, "dia_vencimento": 10}).json()["id"]
    for data in ["2026-10-03", "2026-10-04", "2026-11-03", "2026-11-04"]:
        cliente.post("/transacoes/", headers=ana,
                     json={"tipo": "despesa", "valor": 100, "data": data, "id_categoria": mercado, "id_cartao": cartao})

    fatura = cliente.get(f"/cartoes/{cartao}/fatura/?mes=11&ano=2026", headers=ana).json()
    compras = cliente.get(
        f"/transacoes/?id_cartao={cartao}&data_inicio={fatura['periodo_inicio']}&data_fim={fatura['periodo_fim']}",
        headers=ana,
    ).json()
    assert [c["data"] for c in compras] == ["2026-11-03", "2026-10-04"]
    assert sum(c["valor"] for c in compras) == fatura["valor_total"]
    assert {c["origem"] for c in compras} == {"manual"}

    obj = cliente.post("/objetivos/", headers=ana, json={"nome": "Viagem", "valor_alvo": 1000}).json()
    ap = cliente.post("/aportes/", headers=ana, json={"valor": 50, "data": "2026-11-05", "id_objetivo": obj["id"]}).json()
    assert cliente.get(f"/transacoes/{ap['id_transacao']}", headers=ana).json()["origem"] == "aporte"
