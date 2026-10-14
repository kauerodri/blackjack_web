import random

NAIPES = ["♠", "♥", "♦", "♣"]
VALORES = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

#Gerar baralho com 52 cartas e embaralhar
def criar_baralho():
    baralho = []
    for naipe in NAIPES:
        for valor in VALORES:
            baralho.append({"valor": valor, "naipe": naipe })

    random.shuffle(baralho)
    return baralho

#Retorna o valor em pontos de uma carta individual.
def pontos_da_carta(carta): 
    if carta["valor"] in ["J", "Q", "K"]:
        return 10
    elif carta["valor"] == "A":
        return 11
    else:
        return int(carta["valor"])

#Calcula a pontuacao total da mao considerando o As (11 ou 1).
def pontos_da_mao(mao):
    total = sum(pontos_da_carta(carta) for carta in mao)
    
    # Conta quantos As tem na mao
    quantidade_ases = sum(1 for carta in mao if carta["valor"] == "A")
    
    # Se estourar 21 e tiver As, cada As diminui 10 pontos (passa a valer 1)
    while total > 21 and quantidade_ases > 0:
        total -= 10
        quantidade_ases -= 1
        
    return total


#Tira uma carta do topo do baralho e adiciona na mao.
def comprar_carta(baralho, mao):
    if not baralho:
        baralho.extend(criar_baralho())
    carta = baralho.pop()
    mao.append(carta)
    return carta


#Cria o estado inicial de uma nova partida.
def criar_novo_jogo():
    baralho = criar_baralho()
    mao_jogador = []
    mao_dealer = []
    
    # No Blackjack tradicional, cada um comeca com 2 cartas
    for _ in range(2):
        comprar_carta(baralho, mao_jogador)
        comprar_carta(baralho, mao_dealer)
        
    return {
        "baralho": baralho,
        "jogador": mao_jogador,
        "dealer": mao_dealer,
        "finalizado": False,
        "resultado": ""
    }

#Inteligência do Dealer: compra se for menor que 17 OU se estiver perdendo do jogador.
def jogada_dealer(jogo):
    pontos_jogador = pontos_da_mao(jogo["jogador"])
    
    # Se o jogador já estourou (> 21), o Dealer nem precisa jogar, ele já venceu!
    if pontos_jogador > 21:
        finalizar_partida(jogo)
        return

    while True:
        pontos_dealer = pontos_da_mao(jogo["dealer"])
        
        # 1. Se o Dealer estourar, para imediatamente
        if pontos_dealer > 21:
            break
            
        # 2. Se tem menos de 17, compra por regra básica
        if pontos_dealer < 17:
            comprar_carta(jogo["baralho"], jogo["dealer"])
            
        # 3. Se tem 17 ou mais, mas está perdendo do jogador, ARRISCA!
        elif pontos_dealer < pontos_jogador:
            comprar_carta(jogo["baralho"], jogo["dealer"])
            
        # 4. Se empatou ou superou o jogador, ele segura e para
        else:
            break
            
    finalizar_partida(jogo)


#Compara os pontos e decide quem ganhou.
def finalizar_partida(jogo):
    p_jogador = pontos_da_mao(jogo["jogador"])
    p_dealer = pontos_da_mao(jogo["dealer"])
    
    jogo["finalizado"] = True
    
    if p_jogador > 21:
        jogo["resultado"] = "Você estourou! O Dealer venceu."
    elif p_dealer > 21:
        jogo["resultado"] = "O Dealer estourou! Você venceu!"
    elif p_jogador > p_dealer:
        jogo["resultado"] = f"Você venceu com {p_jogador} pontos contra {p_dealer}!"
    elif p_dealer > p_jogador:
        jogo["resultado"] = f"O Dealer venceu com {p_dealer} pontos contra {p_jogador}."
    else:
        jogo["resultado"] = f"Empate! Ambos com {p_jogador} pontos."


#Executa a ação escolhida pelo jogador: 'comprar' ou 'parar'
def jogada_jogador(jogo, acao):
    if jogo["finalizado"]:
        return

    if acao == "comprar":
        comprar_carta(jogo["baralho"], jogo["jogador"])
        pontos = pontos_da_mao(jogo["jogador"])
        if pontos > 21:
            finalizar_partida(jogo)
    elif acao == "parar":
        # Se o jogador parou, agora é a vez do Dealer jogar
        jogada_dealer(jogo)

if __name__ == "__main__":
    jogo = criar_novo_jogo()
    
    print("--- BEM-VINDO AO 21 (BLACKJACK) ---")
    
    while not jogo["finalizado"]:
        print(f"\nSua mão: {jogo['jogador']} | Pontos: {pontos_da_mao(jogo['jogador'])}")
        print(f"Carta visível do Dealer: {jogo['dealer'][0]}")
        
        escolha = input("Digite [c] para Comprar ou [p] para Parar: ").strip().lower()
        if escolha == "c":
            jogada_jogador(jogo, "comprar")
        elif escolha == "p":
            jogada_jogador(jogo, "parar")
            
    print("\n--- FIM DE JOGO ---")
    print(f"Sua mão final: {jogo['jogador']} ({pontos_da_mao(jogo['jogador'])} pontos)")
    print(f"Mão do Dealer: {jogo['dealer']} ({pontos_da_mao(jogo['dealer'])} pontos)")
    print(f"Resultado: {jogo['resultado']}")
        

        

