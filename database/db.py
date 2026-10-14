import sqlite3
import os

# Caminho para o arquivo do banco de dados ser salvo dentro da pasta database
CAMINHO_BANCO = os.path.join(os.path.dirname(__file__), "cassino.db")


def conectar():
    """Abre uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(CAMINHO_BANCO)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas pelo nome
    return conn


def inicializar_banco():
    """Cria a tabela de histórico de partidas se ela ainda não existir."""
    conn = conectar()
    cursor = conn.cursor()
    
    # Criamos a tabela 'partidas' usando comandos SQL básicos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS partidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resultado TEXT NOT NULL,
            pontos_jogador INTEGER NOT NULL,
            pontos_dealer INTEGER NOT NULL,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 2. NOVA TABELA: Jogadores e seus saldos de fichas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jogadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            saldo INTEGER DEFAULT 1000
        )
    """)
    conn.commit()
    conn.close()


def salvar_partida(resultado, pontos_jogador, pontos_dealer):
    """Grava o resultado de uma partida no banco de dados."""
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO partidas (resultado, pontos_jogador, pontos_dealer)
        VALUES (?, ?, ?)
    """, (resultado, pontos_jogador, pontos_dealer))
    
    conn.commit()
    conn.close()


def obter_estatisticas():
    """Calcula o total de vitórias, derrotas e empates salvos no banco."""
    conn = conectar()
    cursor = conn.cursor()
    
    # Contamos quantas vezes cada resultado aparece
    cursor.execute("SELECT COUNT(*) FROM partidas WHERE resultado = 'vitoria'")
    vitorias = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM partidas WHERE resultado = 'derrota'")
    derrotas = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM partidas WHERE resultado = 'empate'")
    empates = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "vitorias": vitorias,
        "derrotas": derrotas,
        "empates": empates,
        "total": vitorias + derrotas + empates
    }
def obter_ou_criar_saldo(nome):
    """Busca o saldo do jogador. Se ele for novo, cria com $1.000 em fichas."""
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute("SELECT saldo FROM jogadores WHERE nome = ?", (nome,))
    resultado = cursor.fetchone()
    
    if resultado:
        saldo = resultado["saldo"]
    else:
        saldo = 1000
        cursor.execute("INSERT INTO jogadores (nome, saldo) VALUES (?, ?)", (nome, saldo))
        conn.commit()
        
    conn.close()
    return saldo


def atualizar_saldo(nome, novo_saldo):
    """Atualiza a quantidade de fichas do jogador no banco de dados."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE jogadores SET saldo = ? WHERE nome = ?", (novo_saldo, nome))
    conn.commit()
    conn.close()
