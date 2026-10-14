from flask import Flask, render_template, redirect, url_for, session, jsonify, request
from core.game import criar_novo_jogo, jogada_jogador, pontos_da_mao
from database.db import inicializar_banco, salvar_partida, obter_estatisticas
from core.rooms import (
    SALAS, criar_sala, entrar_sala, alterar_aposta, alternar_pronto,
    iniciar_rodada_mesa, executar_jogada_mesa, reiniciar_mesa_apostas
)
app = Flask(__name__)
app.secret_key = "segredo-cassino-21"
inicializar_banco()


@app.route("/")
def index():
    # Se ainda não existe um jogo na sessão, cria um novo
    if "jogo" not in session:
        session["jogo"] = criar_novo_jogo()
        
    jogo = session["jogo"]
    
    # Calculamos os pontos para enviar para a página HTML
    pontos_jogador = pontos_da_mao(jogo["jogador"])
    pontos_dealer = pontos_da_mao(jogo["dealer"])
    #Busca o placar atualizado direto do banco de dados
    estatisticas = obter_estatisticas()
    
    return render_template(
        "mesa.html",
        jogo=jogo,
        pontos_jogador=pontos_jogador,
        pontos_dealer=pontos_dealer,
        estatisticas=estatisticas
    )


@app.route("/jogar/<acao>")
def jogar(acao):
    if "jogo" in session and not session["jogo"]["finalizado"]:
        jogo = session["jogo"]
        jogada_jogador(jogo, acao)
        #Se a partida acabou nessa jogada, gravamos no banco de dados!
        if jogo["finalizado"] and not jogo.get("salvo_no_banco", False):
            pontos_j = pontos_da_mao(jogo["jogador"])
            pontos_d = pontos_da_mao(jogo["dealer"])
            # Identifica quem ganhou pelo texto do resultado
            if "Você venceu" in jogo["resultado"]:
                tipo = "vitoria"
            elif "Dealer venceu" in jogo["resultado"]:
                tipo = "derrota"
            else:
                tipo = "empate"
            
            salvar_partida(tipo, pontos_j, pontos_d)
            jogo["salvo_no_banco"] = True
        
        session.modified = True

    return redirect(url_for("index"))


@app.route("/novo-jogo")
def novo_jogo():
    session["jogo"] = criar_novo_jogo()
    session.modified = True
    return redirect(url_for("index"))

@app.route("/api/jogar/<acao>")
def api_jogar(acao):
    """API para o JavaScript jogar sem recarregar a página."""
    if "jogo" not in session:
        return jsonify({"erro": "Sem jogo ativo"}), 400
        
    jogo = session["jogo"]
    
    # Se a ação for parar, vamos capturar as cartas que o dealer comprar passo a passo
    cartas_iniciais_dealer = list(jogo["dealer"])
    
    jogada_jogador(jogo, acao)
    
    # Descobre quais cartas novas o dealer comprou
    cartas_novas_dealer = jogo["dealer"][len(cartas_iniciais_dealer):]
    
    # Salva no banco se acabou
    if jogo["finalizado"] and not jogo.get("salvo_no_banco", False):
        pontos_j = pontos_da_mao(jogo["jogador"])
        pontos_d = pontos_da_mao(jogo["dealer"])
        tipo = "vitoria" if "Você venceu" in jogo["resultado"] else "derrota" if "Dealer venceu" in jogo["resultado"] else "empate"
        salvar_partida(tipo, pontos_j, pontos_d)
        jogo["salvo_no_banco"] = True

    session.modified = True
    
    return jsonify({
        "jogador": jogo["jogador"],
        "dealer": jogo["dealer"],
        "cartas_novas_dealer": cartas_novas_dealer,
        "pontos_jogador": pontos_da_mao(jogo["jogador"]),
        "pontos_dealer": pontos_da_mao(jogo["dealer"]),
        "finalizado": jogo["finalizado"],
        "resultado": jogo["resultado"],
        "estatisticas": obter_estatisticas()
    })
# --- ROTAS DO MULTIPLAYER (ATÉ 5 JOGADORES VS DEALER) ---

@app.route("/multiplayer")
def multiplayer_lobby():
    return render_template("lobby.html")


@app.route("/multiplayer/criar", methods=["POST"])
def rota_criar_sala():
    nome = request.form.get("nome", "Jogador 1").strip()
    codigo = criar_sala(nome)
    
    session["id_jogador"] = 1
    session["codigo_sala"] = codigo
    return redirect(url_for("ver_sala", codigo=codigo))


@app.route("/multiplayer/entrar", methods=["POST"])
def rota_entrar_sala():
    nome = request.form.get("nome", "Amigo").strip()
    codigo = request.form.get("codigo", "").upper().strip()
    
    sucesso, novo_id = entrar_sala(codigo, nome)
    if not sucesso:
        return render_template("lobby.html", erro=novo_id)
        
    session["id_jogador"] = novo_id
    session["codigo_sala"] = codigo
    return redirect(url_for("ver_sala", codigo=codigo))


@app.route("/sala/<codigo>")
def ver_sala(codigo):
    codigo = codigo.upper().strip()
    if codigo not in SALAS:
        return redirect(url_for("multiplayer_lobby"))
        
    id_jogador = session.get("id_jogador", 1)
    return render_template("mesa_multiplayer.html", codigo=codigo, id_jogador=id_jogador)


@app.route("/api/sala/<codigo>")
def api_obter_sala(codigo):
    codigo = codigo.upper().strip()
    if codigo not in SALAS:
        return jsonify({"erro": "Sala não existe"}), 404
        
    sala = SALAS[codigo]
    id_jogador = session.get("id_jogador", 1)
    
    jogador_vez = sala["jogadores"][sala["turno_idx"]] if sala["estado"] == "jogando" else None
    
    # Prepara a lista com todos os jogadores presentes na mesa
    jogadores_lista = []
    for j in sala["jogadores"]:
        jogadores_lista.append({
            "id": j["id"],
            "nome": j["nome"],
            "saldo": j["saldo"],
            "aposta": j["aposta"],
            "pronto": j.get("pronto", False),
            "mao": j["mao"],
            "pontos": pontos_da_mao(j["mao"]),
            "parou": j["parou"],
            "estourou": j["estourou"],
            "resultado": j["resultado"],
            "ganho": j["ganho"]
        })
        idx_atual = sala["ordem_turnos"][sala["indice_turno"]] if sala["estado"] == "jogando" and sala.get("ordem_turnos") else None
    jogador_vez = sala["jogadores"][idx_atual] if idx_atual is not None else None
    todos_prontos = all(j.get("pronto", False) for j in sala["jogadores"])
    return jsonify({
        "codigo": sala["codigo"],
        "estado": sala["estado"],
        "dono_id": sala["dono_id"],
        "sou_dono": (int(id_jogador) == int(sala["dono_id"])),
        "meu_id": int(id_jogador),
         "todos_prontos": todos_prontos, 
        "jogadores": jogadores_lista,
        "dealer": {
            "mao": sala["dealer"]["mao"],
            "pontos": pontos_da_mao(sala["dealer"]["mao"]),
            "estourou": sala["dealer"]["estourou"]
        },
        "turno_jogador_id": jogador_vez["id"] if jogador_vez else None,
        "minha_vez": (jogador_vez is not None and jogador_vez["id"] == int(id_jogador) and sala["estado"] == "jogando")
    })


@app.route("/api/sala/<codigo>/apostar/<int:valor>")
def api_apostar_sala(codigo, valor):
    codigo = codigo.upper().strip()
    id_jogador = session.get("id_jogador", 1)
    alterar_aposta(codigo, id_jogador, valor)
    return redirect(url_for("api_obter_sala", codigo=codigo))

@app.route("/api/sala/<codigo>/pronto")
def api_alternar_pronto(codigo):
    codigo = codigo.upper().strip()
    id_jogador = session.get("id_jogador", 1)
    alternar_pronto(codigo, id_jogador)
    return redirect(url_for("api_obter_sala", codigo=codigo))


@app.route("/api/sala/<codigo>/iniciar")
def api_iniciar_sala(codigo):
    codigo = codigo.upper().strip()
    iniciar_rodada_mesa(codigo)
    return redirect(url_for("api_obter_sala", codigo=codigo))


@app.route("/api/sala/<codigo>/jogar/<acao>")
def api_jogar_sala(codigo, acao):
    codigo = codigo.upper().strip()
    id_jogador = session.get("id_jogador", 1)
    executar_jogada_mesa(codigo, id_jogador, acao)
    return redirect(url_for("api_obter_sala", codigo=codigo))


@app.route("/api/sala/<codigo>/nova-rodada")
def api_nova_rodada_sala(codigo):
    codigo = codigo.upper().strip()
    reiniciar_mesa_apostas(codigo)
    return redirect(url_for("api_obter_sala", codigo=codigo))


if __name__ == "__main__":
    import os
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta)