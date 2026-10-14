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

// Som orgânico e realista de fichas de cassino (clack-clack)
function tocarSomFicha() {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const t = audioCtx.currentTime;
    // Dois toques rápidos simulando fichas colidindo
    [0, 0.035].forEach(delay => {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        const filter = audioCtx.createBiquadFilter();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(2400, t + delay);
        osc.frequency.exponentialRampToValueAtTime(800, t + delay + 0.04);
        filter.type = 'bandpass';
        filter.frequency.setValueAtTime(3200, t + delay);
        filter.Q.setValueAtTime(3.5, t + delay);
        gain.gain.setValueAtTime(0.4, t + delay);
        gain.gain.exponentialRampToValueAtTime(0.005, t + delay + 0.04);
        osc.connect(filter);
        filter.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(t + delay);
        osc.stop(t + delay + 0.045);
    });
}

function tocarSomVitoria() {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const notas = [261.63, 329.63, 392.00, 523.25];
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

// Criação do elemento visual da carta
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

// Variáveis de controle
const codigoSala = document.getElementById("codigo-sala").innerText.trim();
let totalCartasAnteriores = 0;
let somFinalTocado = false;

// --- CONSULTA EM TEMPO REAL (POLLING A CADA 1 SEGUNDO) ---
async function consultarMesa() {
    try {
        const resposta = await fetch(`/api/sala/${codigoSala}`);
        if (!resposta.ok) return;
        const sala = await resposta.json();

        // 1. Contador de jogadores
        document.getElementById("contador-jogadores").innerText = `${sala.jogadores.length}/5 Jogadores`;

        // 2. Atualizar o Dealer
        const containerDealer = document.getElementById("cartas-dealer");
        containerDealer.innerHTML = "";
        sala.dealer.mao.forEach(c => containerDealer.appendChild(criarElementoCarta(c)));
        document.getElementById("pontos-dealer").innerText = sala.dealer.pontos;

        // 3. Atualizar os Assentos dos Jogadores
        const gradeJogadores = document.getElementById("grade-jogadores");
        gradeJogadores.innerHTML = "";

        let totalCartasAgora = sala.dealer.mao.length;

        sala.jogadores.forEach(j => {
            totalCartasAgora += j.mao.length;
            const isVez = (sala.estado === 'jogando' && sala.turno_jogador_id === j.id);
            const isMeu = (j.id === sala.meu_id);

            const divAssento = document.createElement("div");
            divAssento.className = `assento-jogador ${isVez ? 'vez-ativa' : ''} ${isMeu ? 'meu-assento' : ''}`;

            let statusBadge = "";
            if (j.resultado) {
                statusBadge = `<div class="badge-status" style="background: ${j.ganho > 0 ? '#2e7d32' : '#c62828'}; color: #fff;">${j.resultado}</div>`;
            } else if (j.estourou) {
                statusBadge = `<div class="badge-status" style="background: #c62828; color: #fff;">Estourou! (Bust)</div>`;
            } else if (j.parou) {
                statusBadge = `<div class="badge-status" style="background: #e65100; color: #fff;">Parou</div>`;
            } else if (isVez) {
                statusBadge = `<div class="badge-status" style="background: #f7d070; color: #111;">Na Vez! 🎲</div>`;
            }
            let badgePronto = "";
            if (sala.estado === 'apostas') {
                badgePronto = j.pronto 
                    ? `<div class="badge-status" style="background: #2e7d32; color: #fff;">✅ Aposta Confirmada</div>` 
                    : `<div class="badge-status" style="background: #e65100; color: #fff;">⏳ Escolhendo...</div>`;
            }

            divAssento.innerHTML = `
                <div style="font-weight: bold; color: ${isMeu ? '#f7d070' : '#fff'}; font-size: 1.05rem;">
                    ${j.nome} ${isMeu ? '(Você)' : ''}
                </div>
                <div class="info-saldo-aposta">
                    💰 $${j.saldo} | 🪙 Aposta: $${j.aposta}
                </div>
                <div class="cartas" style="min-height: 90px; justify-content: center; gap: 6px;"></div>
                <div style="color: #e0f2ed; font-size: 0.95rem; margin-top: 4px;">
                    Pontos: <strong>${j.pontos}</strong>
                </div>
                ${statusBadge}
                ${badgePronto}
            `;

            // Adiciona as cartas na mão do jogador
            const divCartas = divAssento.querySelector(".cartas");
            j.mao.forEach(c => divCartas.appendChild(criarElementoCarta(c)));

            gradeJogadores.appendChild(divAssento);
        });

        // Som de carta se o número total de cartas aumentou
        if (totalCartasAnteriores > 0 && totalCartasAgora > totalCartasAnteriores) {
            tocarSomCarta();
        }
        totalCartasAnteriores = totalCartasAgora;

        // 4. CONTROLE DOS PAINÉIS (APOSTA, JOGADA, FIM DE RODADA)
        const painelApostas = document.getElementById("painel-apostas");
        const painelJogada = document.getElementById("painel-jogada");
        const painelProxima = document.getElementById("painel-proxima-rodada");
        const statusTexto = document.getElementById("indicador-status");
        if (sala.estado === "apostas") {
            somFinalTocado = false;
            painelApostas.style.display = "block";
            painelJogada.style.display = "none";
            painelProxima.style.display = "none";
            statusTexto.innerText = "🪙 FASE DE APOSTAS: Escolha suas fichas e confirme!";
            statusTexto.style.borderColor = "#f7d070";
            // Atualiza o botão de confirmação do jogador atual
            const meuJogador = sala.jogadores.find(p => p.id === sala.meu_id);
            const btnConfirmar = document.getElementById("btn-confirmar-aposta");
            if (btnConfirmar && meuJogador) {
                if (meuJogador.pronto) {
                    btnConfirmar.innerText = "Aposta Confirmada! (Mudar?) ✏️";
                    btnConfirmar.style.background = "#555";
                } else {
                    btnConfirmar.innerText = `Confirmar Aposta de $${meuJogador.aposta} ✅`;
                    btnConfirmar.style.background = "#2e7d32";
                }
            }
            // Controle do botão de Iniciar (visível apenas para o Dono da mesa)
            const btnIniciar = document.getElementById("btn-iniciar-rodada");
            const msgAguardando = document.getElementById("msg-aguardando-dono");
            if (sala.sou_dono) {
                btnIniciar.style.display = "inline-block";
                if (sala.todos_prontos) {
                    btnIniciar.style.opacity = "1";
                    btnIniciar.style.pointerEvents = "auto";
                    msgAguardando.innerText = "Todos os jogadores confirmaram! Pode dar as cartas! 🃏";
                    msgAguardando.style.color = "#f7d070";
                } else {
                    btnIniciar.style.opacity = "0.4";
                    btnIniciar.style.pointerEvents = "none";
                    msgAguardando.innerText = "Aguardando todos os convidados confirmarem as apostas...";
                    msgAguardando.style.color = "#a3c2b8";
                }
            } else {
                btnIniciar.style.display = "none";
                msgAguardando.innerText = sala.todos_prontos 
                    ? "Todos prontos! Aguardando o dono dar as cartas..." 
                    : "Aguardando confirmação de todos os jogadores...";
            }
        }  else if (sala.estado === "jogando") {
            painelApostas.style.display = "none";
            painelProxima.style.display = "none";

            if (sala.minha_vez) {
                painelJogada.style.display = "block";
                statusTexto.innerText = "👉 É A SUA VEZ! Compre ou Pare.";
                statusTexto.style.borderColor = "#f7d070";
            } else {
                painelJogada.style.display = "none";
                const jogadorVez = sala.jogadores.find(p => p.id === sala.turno_jogador_id);
                const nomeVez = jogadorVez ? jogadorVez.nome : "outro jogador";
                statusTexto.innerText = `⏳ Vez de ${nomeVez}... aguarde!`;
                statusTexto.style.borderColor = "#a3c2b8";
            }
        } else if (sala.estado === "finalizado") {
            painelApostas.style.display = "none";
            painelJogada.style.display = "none";
            painelProxima.style.display = "block";
            statusTexto.innerText = "🏁 RODADA FINALIZADA! O Dealer pagou as apostas.";
            statusTexto.style.borderColor = "#2e7d32";

            if (!somFinalTocado) {
                somFinalTocado = true;
                const meuJogador = sala.jogadores.find(p => p.id === sala.meu_id);
                if (meuJogador && meuJogador.ganho > 0) {
                    tocarSomVitoria();
                } else {
                    tocarSomDerrota();
                }
            }
        }
    } catch (erro) {
        console.error("Erro na atualização da mesa:", erro);
    }
}

// --- AÇÕES DO JOGADOR ---
async function mudarAposta(valor) {
    tocarSomFicha();
    await fetch(`/api/sala/${codigoSala}/apostar/${valor}`);
    await consultarMesa();
}

async function iniciarRodada() {
    await fetch(`/api/sala/${codigoSala}/iniciar`);
    await consultarMesa();
}

async function jogarMulti(acao) {
    const btnC = document.getElementById("btn-comprar");
    const btnP = document.getElementById("btn-parar");
    btnC.style.pointerEvents = "none";
    btnP.style.pointerEvents = "none";

    try {
        await fetch(`/api/sala/${codigoSala}/jogar/${acao}`);
        await consultarMesa();
    } catch (erro) {
        console.error("Erro ao jogar:", erro);
    } finally {
        btnC.style.pointerEvents = "auto";
        btnP.style.pointerEvents = "auto";
    }
}

async function proximaRodada() {
    await fetch(`/api/sala/${codigoSala}/nova-rodada`);
    somFinalTocado = false;
    await consultarMesa();
}

// Consulta a mesa a cada 1 segundo (tempo real)
setInterval(consultarMesa, 1000);
consultarMesa();

async function confirmarAposta() {
    tocarSomFicha();
    await fetch(`/api/sala/${codigoSala}/pronto`);
    await consultarMesa();
}
