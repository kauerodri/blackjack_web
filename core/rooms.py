import random
import string
from core.game import criar_baralho, comprar_carta, pontos_da_mao
from database.db import obter_ou_criar_saldo, atualizar_saldo

SALAS = {}


def gerar_codigo_sala():
    while True:
        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        if codigo not in SALAS:
            return codigo


def criar_sala(nome_jogador):
    """Cria uma sala com até 5 assentos contra o Dealer."""
    codigo = gerar_codigo_sala()
    saldo = obter_ou_criar_saldo(nome_jogador or "Jogador 1")
    
    SALAS[codigo] = {
        "codigo": codigo,
        "baralho": criar_baralho(),
        "estado": "apostas",  # 'apostas', 'jogando', 'finalizado', 'abandonado'
        "dono_id": 1,
        "primeiro_jogador_idx": 0,  # Controla a rotação horária de quem começa
        "ordem_turnos": [],
        "indice_turno": 0,
        "jogadores": [
            {
                "id": 1,
                "nome": nome_jogador or "Jogador 1",
                "saldo": saldo,
                "aposta": 50,  # Aposta padrão inicial
                "pronto": False,
                "mao": [],
                "parou": False,
                "estourou": False,
                "resultado": "",
                "ganho": 0
            }
        ],
        "dealer": {
            "mao": [],
            "pontos": 0,
            "estourou": False
        },
        "turno_idx": 0,
        "proximo_id": 2
    }
    return codigo


def entrar_sala(codigo, nome_jogador):
    """Adiciona um novo amigo na mesa (máximo de 5 jogadores)."""
    codigo = codigo.upper().strip()
    if codigo not in SALAS:
        return False, "Sala não encontrada!"
        
    sala = SALAS[codigo]
    
    if len(sala["jogadores"]) >= 5:
        return False, "Esta mesa já atingiu o limite máximo de 5 jogadores!"
        
    if sala["estado"] != "apostas":
        return False, "A partida já começou! Aguarde a próxima rodada no lobby."
        
    nome = nome_jogador or f"Jogador {sala['proximo_id']}"
    saldo = obter_ou_criar_saldo(nome)
    
    novo_jogador = {
        "id": sala["proximo_id"],
        "nome": nome,
        "saldo": saldo,
        "aposta": 50,
        "pronto": False, 
        "mao": [],
        "parou": False,
        "estourou": False,
        "resultado": "",
        "ganho": 0
    }
    
    sala["jogadores"].append(novo_jogador)
    sala["proximo_id"] += 1
    return True, novo_jogador["id"]

def alterar_aposta(codigo, id_jogador, valor):
    """Permite ao jogador ajustar a aposta antes das cartas serem dadas."""
    if codigo not in SALAS:
        return
    sala = SALAS[codigo]
    for j in sala["jogadores"]:
        if j["id"] == int(id_jogador):
            if 10 <= valor <= j["saldo"]:
                j["aposta"] = valor
            break


def alternar_pronto(codigo, id_jogador):
    """Marca ou desmarca o jogador como 'Pronto' com a aposta confirmada."""
    if codigo not in SALAS:
        return
    sala = SALAS[codigo]
    for j in sala["jogadores"]:
        if j["id"] == int(id_jogador):
            j["pronto"] = not j.get("pronto", False)
            break


def iniciar_rodada_mesa(codigo):
    """Gera a ordem em sentido horário e distribui as cartas."""
    if codigo not in SALAS:
        return
    sala = SALAS[codigo]
    
    # Só começa se todos estiverem prontos!
    if not all(j["pronto"] for j in sala["jogadores"]):
        return
        
    sala["baralho"] = criar_baralho()
    sala["dealer"] = {"mao": [], "pontos": 0, "estourou": False}
    
    # ROTAÇÃO HORÁRIA: Gera a sequência de quem joga nesta rodada
    qtd = len(sala["jogadores"])
    inicio = sala["primeiro_jogador_idx"] % qtd
    sala["ordem_turnos"] = [(inicio + i) % qtd for i in range(qtd)]
    sala["indice_turno"] = 0
    
    for j in sala["jogadores"]:
        j["saldo"] -= j["aposta"]
        atualizar_saldo(j["nome"], j["saldo"])
        j["mao"] = []
        j["parou"] = False
        j["estourou"] = False
        j["resultado"] = ""
        j["ganho"] = 0
        
        comprar_carta(sala["baralho"], j["mao"])
        comprar_carta(sala["baralho"], j["mao"])
        
    comprar_carta(sala["baralho"], sala["dealer"]["mao"])
    comprar_carta(sala["baralho"], sala["dealer"]["mao"])
    
    sala["estado"] = "jogando"


def executar_jogada_mesa(codigo, id_jogador, acao):
    if codigo not in SALAS or SALAS[codigo]["estado"] != "jogando":
        return
    sala = SALAS[codigo]
    
    # Jogador da vez seguindo a ordem horária
    idx_atual = sala["ordem_turnos"][sala["indice_turno"]]
    jogador_vez = sala["jogadores"][idx_atual]
    
    if jogador_vez["id"] != int(id_jogador):
        return
        
    if acao == "comprar":
        comprar_carta(sala["baralho"], jogador_vez["mao"])
        if pontos_da_mao(jogador_vez["mao"]) > 21:
            jogador_vez["estourou"] = True
            jogador_vez["parou"] = True
            avancar_turno_mesa(sala)
    elif acao == "parar":
        jogador_vez["parou"] = True
        avancar_turno_mesa(sala)

def avancar_turno_mesa(sala):
    sala["indice_turno"] += 1
    if sala["indice_turno"] >= len(sala["ordem_turnos"]):
        jogar_dealer_mesa(sala)


def jogar_dealer_mesa(sala):
    """O Dealer compra cartas e paga os vencedores."""
    # O Dealer compra até ter pelo menos 17 pontos
    while pontos_da_mao(sala["dealer"]["mao"]) < 17:
        comprar_carta(sala["baralho"], sala["dealer"]["mao"])
        
    pontos_dealer = pontos_da_mao(sala["dealer"]["mao"])
    dealer_estourou = pontos_dealer > 21
    sala["dealer"]["pontos"] = pontos_dealer
    sala["dealer"]["estourou"] = dealer_estourou
    
    # Calcula os ganhos de cada jogador da mesa
    for j in sala["jogadores"]:
        pontos_j = pontos_da_mao(j["mao"])
        blackjack_natural = (len(j["mao"]) == 2 and pontos_j == 21)
        
        if j["estourou"]:
            j["resultado"] = "Estourou! Perdeu a aposta."
            j["ganho"] = 0
        elif dealer_estourou:
            if blackjack_natural:
                j["ganho"] = int(j["aposta"] * 2.5)
                j["resultado"] = f"BLACKJACK! Ganhou ${j['ganho']} fichas!"
            else:
                j["ganho"] = j["aposta"] * 2
                j["resultado"] = f"Dealer estourou! Ganhou ${j['ganho']} fichas!"
        elif pontos_j > pontos_dealer:
            if blackjack_natural:
                j["ganho"] = int(j["aposta"] * 2.5)
                j["resultado"] = f"BLACKJACK! Ganhou ${j['ganho']} fichas!"
            else:
                j["ganho"] = j["aposta"] * 2
                j["resultado"] = f"Venceu o Dealer! Ganhou ${j['ganho']} fichas!"
        elif pontos_j == pontos_dealer:
            j["ganho"] = j["aposta"]
            j["resultado"] = "Empatou com o Dealer (Aposta devolvida)."
        else:
            j["ganho"] = 0
            j["resultado"] = f"Perdeu para os {pontos_dealer} pontos do Dealer."
            
        # Paga o jogador e grava no SQLite
        if j["ganho"] > 0:
            j["saldo"] += j["ganho"]
            atualizar_saldo(j["nome"], j["saldo"])
            
    sala["estado"] = "finalizado"


def reiniciar_mesa_apostas(codigo):
    if codigo not in SALAS:
        return
    sala = SALAS[codigo]
    sala["estado"] = "apostas"
    sala["dealer"]["mao"] = []
    
    # Roda o primeiro jogador para o próximo no sentido horário na rodada seguinte!
    sala["primeiro_jogador_idx"] = (sala["primeiro_jogador_idx"] + 1) % len(sala["jogadores"])
    
    for j in sala["jogadores"]:
        j["pronto"] = False  # Reseta o botão de confirmação
        j["mao"] = []
        j["parou"] = False
        j["estourou"] = False
        j["resultado"] = ""
        j["ganho"] = 0