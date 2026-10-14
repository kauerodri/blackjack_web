// --- SISTEMA DE EFEITOS SONOROS (WEB AUDIO API) ---
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

function tocarSomCarta() {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(350, audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(100, audioCtx.currentTime + 0.1);
    gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
    gain.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 0.1);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.1);
}

function tocarSomVitoria() {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const notas = [261.63, 329.63, 392.00, 523.25]; // Dó, Mi, Sol, Dó agudo
    notas.forEach((nota, i) => {
        setTimeout(() => {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.frequency.setValueAtTime(nota, audioCtx.currentTime);
            gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
            gain.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 0.25);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.25);
        }, i * 120);
    });
}

function tocarSomDerrota() {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(180, audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(60, audioCtx.currentTime + 0.4);
    gain.gain.setValueAtTime(0.25, audioCtx.currentTime);
    gain.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.4);
}

// Função auxiliar para criar a pausa de suspense (em milissegundos)
const esperar = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// --- CRIAÇÃO VISUAL DA CARTA ---
function criarElementoCarta(carta) {
    const div = document.createElement("div");
    const eVermelha = (carta.naipe === '♥' || carta.naipe === '♦');
    div.className = `carta ${eVermelha ? 'vermelha' : ''}`;
    div.innerHTML = `
        <span class="valor-topo">${carta.valor}</span>
        <span class="naipe-centro">${carta.naipe}</span>
        <span class="valor-rodape">${carta.valor}</span>
    `;
    return div;
}

// --- JOGADAS VIA API ---
async function jogarAcao(acao) {
    const btnComprar = document.getElementById("btn-comprar");
    const btnParar = document.getElementById("btn-parar");

    if (btnComprar && btnParar) {
        btnComprar.style.pointerEvents = "none";
        btnParar.style.pointerEvents = "none";
    }

    try {
        const resposta = await fetch(`/api/jogar/${acao}`);
        const dados = await resposta.json();

        if (acao === 'comprar') {
            tocarSomCarta();
            atualizarMesa(dados);
        } else if (acao === 'parar') {
            // Se parou, vamos animar o Dealer puxando carta a carta!
            await animarDealer(dados);
        }
    } catch (erro) {
        console.error("Erro na jogada:", erro);
    }
}

async function animarDealer(dados) {
    const areaCartasDealer = document.getElementById("cartas-dealer");
    const labelStatus = document.getElementById("status-dealer");
    
    if (labelStatus) labelStatus.innerText = " (Dealer pensando...)";

    // Puxa cada carta nova com suspense
    for (const carta of dados.cartas_novas_dealer) {
        await esperar(800);
        tocarSomCarta();
        areaCartasDealer.appendChild(criarElementoCarta(carta));
    }

    await esperar(500);
    if (labelStatus) labelStatus.innerText = "";
    
    // Atualiza pontuação e finaliza
    atualizarMesa(dados);
}

function atualizarMesa(dados) {
    // 1. Atualiza cartas do jogador
    const containerJogador = document.getElementById("cartas-jogador");
    containerJogador.innerHTML = "";
    dados.jogador.forEach(carta => containerJogador.appendChild(criarElementoCarta(carta)));
    document.getElementById("pontos-jogador").innerText = dados.pontos_jogador;

    // 2. Atualiza cartas do dealer
    const containerDealer = document.getElementById("cartas-dealer");
    containerDealer.innerHTML = "";
    dados.dealer.forEach(carta => containerDealer.appendChild(criarElementoCarta(carta)));
    document.getElementById("pontos-dealer").innerText = dados.pontos_dealer;

    // 3. Atualiza estatísticas do banco
    if (dados.estatisticas) {
        document.getElementById("stat-vitorias").innerText = dados.estatisticas.vitorias;
        document.getElementById("stat-derrotas").innerText = dados.estatisticas.derrotas;
        document.getElementById("stat-empates").innerText = dados.estatisticas.empates;
        document.getElementById("stat-total").innerText = dados.estatisticas.total;
    }

    // 4. Se o jogo acabou, toca o som e mostra o resultado
    if (dados.finalizado) {
        const painelResultado = document.getElementById("painel-resultado");
        const textoResultado = document.getElementById("texto-resultado");
        const controles = document.getElementById("controles-jogando");

        textoResultado.innerText = dados.resultado;
        painelResultado.style.display = "block";
        if (controles) controles.style.display = "none";

        if (dados.resultado.includes("Você venceu")) {
            tocarSomVitoria();
        } else if (dados.resultado.includes("Dealer venceu") || dados.resultado.includes("estourou")) {
            tocarSomDerrota();
        }
    } else {
        const btnComprar = document.getElementById("btn-comprar");
        const btnParar = document.getElementById("btn-parar");
        if (btnComprar && btnParar) {
            btnComprar.style.pointerEvents = "auto";
            btnParar.style.pointerEvents = "auto";
        }
    }
}