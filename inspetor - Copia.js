/**
 * Inspetor de Elementos (apenas Desktop)
 * Usa detecção automática de dispositivo
 * Inclui Monitor de Cliques para rastrear funções
 */

(function() {
    'use strict';

    let inspetorAtivo = false;
    let elementoDestacado = null;
    let popup = null;
    let overlay = null;
    let btnInspetor = null;
    let funcaoCapturada = null; // Armazena função capturada no clique esquerdo

    // Registro de event listeners (para rastrear)
    const eventListenersMap = new WeakMap();

    // Cores do tema Gasto Seguro
    const CORES = {
        destaque: '#26A95E',
        fundo: '#1e293b',
        texto: '#f8fafc',
        hover: '#0F8B4A',
        monitor: '#f59e0b'
    };

    // =============================================
    // MONKEY-PATCH addEventListener para rastrear
    // =============================================
    const originalAddEventListener = EventTarget.prototype.addEventListener;
    EventTarget.prototype.addEventListener = function(type, listener, options) {
        // Registrar o listener apenas para elementos DOM válidos
        try {
            if (this && typeof this === 'object' && this instanceof Element) {
                if (!eventListenersMap.has(this)) {
                    eventListenersMap.set(this, []);
                }
                const listeners = eventListenersMap.get(this);
                listeners.push({
                    type: type,
                    listener: listener,
                    name: (typeof listener === 'function' ? listener.name : '') || 'anonima'
                });
            }
        } catch (e) {
            // Ignorar erros silenciosamente
        }

        // Chamar original
        return originalAddEventListener.call(this, type, listener, options);
    };

    // =============================================
    // DETECÇÃO AUTOMÁTICA DE DISPOSITIVO
    // =============================================

    function isDesktop() {
        return window.innerWidth > 1024 &&
               !/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    function detectarEInicializar() {
        const tipo = isDesktop() ? 'desktop' : 'mobile';

        // Aplicar modo no body
        document.body.setAttribute('data-dispositivo', tipo);
        document.body.classList.remove('modo-desktop', 'modo-mobile');
        document.body.classList.add(`modo-${tipo}`);

        // Inspetor só em Desktop
        if (tipo === 'desktop') {
            inicializarInspetor();
            console.log('🔍 Inspetor carregado (Desktop detectado)');
        } else {
            console.log('📱 Mobile detectado - Inspetor desativado');
        }
    }

    // =============================================
    // INSPETOR (apenas Desktop)
    // =============================================

    function inicializarInspetor() {
        criarBotaoInspetor();
        criarOverlay();
        criarPopup();
        console.log('🔍 Inspetor carregado (Desktop only)');
    }

    function criarBotaoInspetor() {
        btnInspetor = document.createElement('button');
        btnInspetor.id = 'btn-inspetor';
        btnInspetor.innerHTML = '🔍 Inspetor';
        btnInspetor.title = 'Ativar/Desativar Modo Inspetor';
        btnInspetor.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 99999;
            padding: 10px 16px;
            background: ${CORES.fundo};
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            transition: all 0.2s ease;
            font-family: Montserrat, system-ui, sans-serif;
        `;
        btnInspetor.addEventListener('click', toggleInspetor);
        btnInspetor.addEventListener('mouseenter', () => {
            if (!inspetorAtivo) btnInspetor.style.background = CORES.destaque;
        });
        btnInspetor.addEventListener('mouseleave', () => {
            if (!inspetorAtivo) btnInspetor.style.background = CORES.fundo;
        });
        document.body.appendChild(btnInspetor);
    }

    // Gerar seletor simples do elemento
    function obterSeletor(el) {
        if (!el || !el.tagName) return 'desconhecido';
        let seletor = el.tagName.toLowerCase();
        if (el.id) seletor += '#' + el.id;
        else if (el.classList && el.classList.length > 0) seletor += '.' + el.classList[0];
        return seletor;
    }

    // Obter informações de funções/eventos do elemento (busca também nos pais)
    function obterInfoFuncao(el) {
        let funcao = 'nenhuma';
        let tipo = '';
        let elementoComFuncao = el;

        // Buscar no elemento e nos pais (até 5 níveis)
        let atual = el;
        let nivel = 0;

        while (atual && nivel < 5 && funcao === 'nenhuma') {
            // 1. Verificar atributo onclick
            const onclick = atual.getAttribute && atual.getAttribute('onclick');
            if (onclick) {
                const match = onclick.match(/^(\w+)\s*\(/);
                funcao = match ? match[1] + '()' : onclick.substring(0, 40);
                tipo = nivel === 0 ? 'onclick' : `onclick (pai: ${obterSeletor(atual)})`;
                elementoComFuncao = atual;
                break;
            }

            // 2. Verificar listeners registrados
            const listeners = eventListenersMap.get(atual) || [];
            const clickListeners = listeners.filter(l => l.type === 'click');

            if (clickListeners.length > 0) {
                funcao = clickListeners.map(l => l.name + '()').join(', ');
                tipo = nivel === 0 ? 'addEventListener' : `addEventListener (pai: ${obterSeletor(atual)})`;
                elementoComFuncao = atual;
                break;
            }

            // 3. Verificar onclick property
            if (atual.onclick && typeof atual.onclick === 'function') {
                funcao = (atual.onclick.name || 'anonima') + '()';
                tipo = nivel === 0 ? 'onclick property' : `onclick property (pai: ${obterSeletor(atual)})`;
                elementoComFuncao = atual;
                break;
            }

            atual = atual.parentElement;
            nivel++;
        }

        // 4. Verificar se tem href (links)
        if (el.tagName === 'A' && el.href && funcao === 'nenhuma') {
            funcao = 'navegar → ' + (el.href.length > 30 ? el.href.substring(0, 30) + '...' : el.href);
            tipo = 'link';
        }

        // Todos os listeners do elemento clicado
        const listeners = eventListenersMap.get(el) || [];
        const todosListeners = listeners.map(l => `${l.type}: ${l.name}()`).join(', ') || 'nenhum';

        return { funcao, tipo, todosListeners };
    }

    function criarOverlay() {
        overlay = document.createElement('div');
        overlay.id = 'inspetor-overlay';
        overlay.style.cssText = `
            position: fixed;
            pointer-events: none;
            z-index: 99997;
            border: 2px solid ${CORES.destaque};
            background: rgba(38, 169, 94, 0.15);
            display: none;
        `;
        document.body.appendChild(overlay);
    }

    function criarPopup() {
        popup = document.createElement('div');
        popup.id = 'inspetor-popup';
        popup.style.cssText = `
            position: fixed;
            z-index: 99998;
            background: ${CORES.fundo};
            color: ${CORES.texto};
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            max-width: 420px;
            min-width: 320px;
            font-family: Montserrat, system-ui, sans-serif;
            font-size: 13px;
            display: none;
            overflow: hidden;
        `;
        document.body.appendChild(popup);
    }

    function toggleInspetor() {
        inspetorAtivo = !inspetorAtivo;

        if (inspetorAtivo) {
            btnInspetor.innerHTML = '✖ Fechar';
            btnInspetor.style.background = '#ef4444';
            funcaoCapturada = null; // Limpar captura anterior
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('contextmenu', onRightClick);
            document.addEventListener('click', onLeftClick, true); // Capture phase
            document.addEventListener('click', fecharPopup);
            showToast('🔍 Inspetor ATIVADO - Clique esquerdo captura função, direito inspeciona');
        } else {
            btnInspetor.innerHTML = '🔍 Inspetor';
            btnInspetor.style.background = CORES.fundo;
            funcaoCapturada = null;
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('contextmenu', onRightClick);
            document.removeEventListener('click', onLeftClick, true);
            document.removeEventListener('click', fecharPopup);
            overlay.style.display = 'none';
            popup.style.display = 'none';
            showToast('🔍 Inspetor DESATIVADO');
        }
    }

    // Captura função no clique esquerdo (sem bloquear)
    function onLeftClick(e) {
        if (!inspetorAtivo) return;
        if (e.target === btnInspetor || e.target === popup || popup.contains(e.target)) return;

        const el = e.target;
        const info = obterInfoFuncao(el);

        // Armazenar informação capturada
        funcaoCapturada = {
            elemento: el,
            seletor: obterSeletor(el),
            funcao: info.funcao,
            tipo: info.tipo,
            todosListeners: info.todosListeners,
            timestamp: new Date().toLocaleTimeString()
        };

        // Toast informativo
        if (info.funcao !== 'nenhuma') {
            showToast(`⚡ Capturado: ${info.funcao}`);
        } else {
            showToast(`⚡ Clique em: ${obterSeletor(el).substring(0, 30)}`);
        }

        // Log no console
        console.log('⚡ Função capturada:', funcaoCapturada);
    }

    function onMouseMove(e) {
        if (!inspetorAtivo) return;

        const el = document.elementFromPoint(e.clientX, e.clientY);
        if (!el || el === btnInspetor || el === popup || el === overlay || popup.contains(el)) return;

        elementoDestacado = el;
        const rect = el.getBoundingClientRect();

        overlay.style.display = 'block';
        overlay.style.top = rect.top + 'px';
        overlay.style.left = rect.left + 'px';
        overlay.style.width = rect.width + 'px';
        overlay.style.height = rect.height + 'px';
    }

    function onRightClick(e) {
        if (!inspetorAtivo) return;
        if (e.target === btnInspetor || e.target === popup || popup.contains(e.target)) return;

        e.preventDefault();
        elementoDestacado = e.target;

        const info = getElementInfo(elementoDestacado);
        renderPopup(info, e.clientX, e.clientY);
    }

    function fecharPopup(e) {
        if (popup && popup.style.display === 'block') {
            if (!popup.contains(e.target)) {
                popup.style.display = 'none';
            }
        }
    }

    function detectarTelaAtiva() {
        const sidebarItem = document.querySelector('.sidebar-item.active');
        if (sidebarItem) return sidebarItem.textContent.trim();
        return 'Inicio';
    }

    // Capturar eventos JavaScript do elemento
    function capturarEventos(el) {
        const eventos = [];

        // 1. Atributos inline (onclick, onchange, etc)
        const eventosInline = ['onclick', 'onchange', 'onmouseover', 'onmouseout',
                               'onfocus', 'onblur', 'onsubmit', 'onkeyup', 'onkeydown',
                               'oninput', 'ondblclick'];

        eventosInline.forEach(attr => {
            const valor = el.getAttribute(attr);
            if (valor) {
                // Extrair nome da função (ex: "salvarDados()" de "salvarDados(this)")
                const match = valor.match(/^(\w+)\s*\(/);
                const funcName = match ? match[1] + '()' : valor.substring(0, 30);
                eventos.push(`${attr.replace('on', '')}: ${funcName}`);
            }
        });

        // 2. Propriedades de evento no elemento
        const tiposEventos = ['click', 'change', 'mouseover', 'mouseout',
                              'focus', 'blur', 'submit', 'input'];

        tiposEventos.forEach(tipo => {
            const propName = 'on' + tipo;
            if (el[propName] && typeof el[propName] === 'function') {
                const funcName = el[propName].name || 'anonima';
                if (!eventos.some(e => e.startsWith(tipo + ':'))) {
                    eventos.push(`${tipo}: ${funcName}()`);
                }
            }
        });

        return eventos.length > 0 ? eventos.join(' | ') : 'nenhum';
    }

    function getElementInfo(el) {
        const computed = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();

        let seletor = el.tagName.toLowerCase();
        if (el.id) seletor += '#' + el.id;
        if (el.classList.length > 0) {
            seletor += '.' + Array.from(el.classList).join('.');
        }

        let hierarquia = [];
        let parent = el;
        while (parent && parent !== document.body && hierarquia.length < 4) {
            let nome = parent.tagName.toLowerCase();
            if (parent.id) nome += '#' + parent.id;
            else if (parent.classList.length > 0) nome += '.' + parent.classList[0];
            hierarquia.unshift(nome);
            parent = parent.parentElement;
        }

        // Calcular distancias da borda da tela
        const distEsquerda = Math.round(rect.left);
        const distDireita = Math.round(window.innerWidth - rect.right);
        const distTopo = Math.round(rect.top);
        const distBaixo = Math.round(window.innerHeight - rect.bottom);

        // Capturar conteudo de texto do elemento
        let conteudo = '';

        // Primeiro tenta pegar texto direto do elemento
        const textosDiretos = Array.from(el.childNodes)
            .filter(node => node.nodeType === Node.TEXT_NODE)
            .map(node => node.textContent.trim())
            .filter(t => t.length > 0);

        if (textosDiretos.length > 0) {
            conteudo = textosDiretos.join(' ');
        } else {
            // Se nao tem texto direto, pega o texto visivel (limitado)
            conteudo = el.textContent?.trim() || '';
        }

        // Limitar tamanho e limpar quebras de linha
        conteudo = conteudo.replace(/\s+/g, ' ').substring(0, 100);
        if (el.textContent?.trim().length > 100) conteudo += '...';

        // Se for input/textarea, pegar value ou placeholder
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            conteudo = el.value || el.placeholder || '-';
        }

        // Se for imagem, pegar alt
        if (el.tagName === 'IMG') {
            conteudo = el.alt || el.src?.split('/').pop() || '-';
        }

        // Capturar eventos JavaScript
        const eventos = capturarEventos(el);

        return {
            telaAtiva: detectarTelaAtiva(),
            tag: el.tagName.toLowerCase(),
            id: el.id || '-',
            classes: el.classList.length > 0 ? Array.from(el.classList).join(' ') : '-',
            seletor: seletor,
            conteudo: conteudo || '-',
            eventos: eventos,
            largura: Math.round(rect.width) + 'px',
            altura: Math.round(rect.height) + 'px',
            padding: computed.padding,
            margin: computed.margin,
            background: computed.backgroundColor,
            corTexto: computed.color,
            borderRadius: computed.borderRadius,
            fonte: computed.fontFamily.split(',')[0].replace(/"/g, ''),
            tamanhoFonte: computed.fontSize,
            pesoFonte: computed.fontWeight,
            hierarquia: hierarquia.join(' > '),
            distEsquerda: distEsquerda + 'px',
            distDireita: distDireita + 'px',
            distTopo: distTopo + 'px',
            distBaixo: distBaixo + 'px',
            telaLargura: window.innerWidth + 'px',
            telaAltura: window.innerHeight + 'px'
        };
    }

    function renderPopup(info, x, y) {
        popup.innerHTML = `
            <div style="background: linear-gradient(135deg, ${CORES.destaque} 0%, ${CORES.hover} 100%); padding: 12px 16px; font-weight: 600; display: flex; justify-content: space-between; align-items: center;">
                <span>🔍 Inspetor</span>
                <button onclick="document.getElementById('inspetor-popup').style.display='none'" style="background: rgba(255,255,255,0.2); border: none; color: white; width: 24px; height: 24px; border-radius: 4px; cursor: pointer;">✖</button>
            </div>
            <div style="padding: 16px; max-height: 400px; overflow-y: auto;">
                <div style="margin-bottom: 16px; padding: 10px; background: #0f172a; border-radius: 8px;">
                    <div style="color: #fbbf24; font-size: 11px; text-transform: uppercase; margin-bottom: 6px;">Contexto</div>
                    <div style="display: grid; grid-template-columns: 70px 1fr; gap: 4px; font-size: 12px;">
                        <span style="color: #94a3b8;">Tela:</span><span style="color: #4ade80;">${info.telaAtiva}</span>
                    </div>
                </div>

                <div style="margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #334155;">
                    <div style="color: #94a3b8; font-size: 11px; text-transform: uppercase; margin-bottom: 6px;">Elemento</div>
                    <div style="display: grid; grid-template-columns: 80px 1fr; gap: 6px;">
                        <span style="color: #94a3b8;">Tag:</span><span style="color: #60a5fa;">&lt;${info.tag}&gt;</span>
                        <span style="color: #94a3b8;">ID:</span><span style="color: #fbbf24;">${info.id}</span>
                        <span style="color: #94a3b8;">Classes:</span><span style="color: #34d399; word-break: break-all;">${info.classes}</span>
                    </div>
                </div>

                <div style="margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #334155;">
                    <div style="color: #94a3b8; font-size: 11px; text-transform: uppercase; margin-bottom: 6px;">Seletor CSS</div>
                    <code style="display: block; background: #0f172a; padding: 8px 12px; border-radius: 6px; font-size: 12px; color: #e879f9; word-break: break-all;">${info.seletor}</code>
                </div>

                <div style="margin-bottom: 16px; padding: 10px; background: #0f172a; border-radius: 8px;">
                    <div style="color: #fbbf24; font-size: 11px; text-transform: uppercase; margin-bottom: 6px;">Conteudo</div>
                    <div style="color: #f8fafc; font-size: 13px; word-break: break-word;">${info.conteudo}</div>
                </div>

                ${funcaoCapturada ? `
                <div style="margin-bottom: 16px; padding: 10px; background: #2d1f0f; border-radius: 8px; border-left: 3px solid ${CORES.monitor};">
                    <div style="color: ${CORES.monitor}; font-size: 11px; text-transform: uppercase; margin-bottom: 6px;">⚡ Função Capturada (Clique)</div>
                    <div style="color: #fcd34d; font-size: 14px; font-weight: 600; margin-bottom: 4px;">${funcaoCapturada.funcao}</div>
                    <div style="color: #94a3b8; font-size: 11px;">via ${funcaoCapturada.tipo || 'clique'} em ${funcaoCapturada.seletor}</div>
                    <div style="color: #64748b; font-size: 10px; margin-top: 4px;">${funcaoCapturada.timestamp}</div>
                </div>
                ` : ''}

                <div style="margin-bottom: 16px; padding: 10px; background: ${info.eventos !== 'nenhum' ? '#1e3a2f' : '#0f172a'}; border-radius: 8px; border-left: 3px solid ${info.eventos !== 'nenhum' ? '#4ade80' : '#475569'};">
                    <div style="color: #4ade80; font-size: 11px; text-transform: uppercase; margin-bottom: 6px;">⚡ Eventos JS (Elemento)</div>
                    <div style="color: ${info.eventos !== 'nenhum' ? '#86efac' : '#64748b'}; font-size: 12px; word-break: break-word;">${info.eventos}</div>
                </div>

                <div style="margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #334155;">
                    <div style="color: #94a3b8; font-size: 11px; text-transform: uppercase; margin-bottom: 6px;">Dimensoes e Espacamento</div>
                    <div style="display: grid; grid-template-columns: 80px 1fr; gap: 6px;">
                        <span style="color: #94a3b8;">Tamanho:</span><span>${info.largura} x ${info.altura}</span>
                        <span style="color: #94a3b8;">Padding:</span><span style="color: #4ade80;">${info.padding}</span>
                        <span style="color: #94a3b8;">Margin:</span><span style="color: #fb923c;">${info.margin}</span>
                    </div>
                </div>

                <div style="margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #334155;">
                    <div style="color: #94a3b8; font-size: 11px; text-transform: uppercase; margin-bottom: 6px;">Posicao na Tela (${info.telaLargura} x ${info.telaAltura})</div>
                    <div style="display: grid; grid-template-columns: 80px 1fr; gap: 6px;">
                        <span style="color: #94a3b8;">Esquerda:</span><span style="color: #38bdf8;">${info.distEsquerda}</span>
                        <span style="color: #94a3b8;">Direita:</span><span style="color: #38bdf8;">${info.distDireita}</span>
                        <span style="color: #94a3b8;">Topo:</span><span style="color: #38bdf8;">${info.distTopo}</span>
                        <span style="color: #94a3b8;">Baixo:</span><span style="color: #38bdf8;">${info.distBaixo}</span>
                    </div>
                </div>

                <div style="margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #334155;">
                    <div style="color: #94a3b8; font-size: 11px; text-transform: uppercase; margin-bottom: 6px;">Estilos</div>
                    <div style="display: grid; grid-template-columns: 80px 1fr; gap: 6px;">
                        <span style="color: #94a3b8;">Background:</span><span style="display: flex; align-items: center; gap: 6px;"><span style="width: 14px; height: 14px; border-radius: 3px; background: ${info.background}; border: 1px solid #475569;"></span>${info.background}</span>
                        <span style="color: #94a3b8;">Cor Texto:</span><span style="display: flex; align-items: center; gap: 6px;"><span style="width: 14px; height: 14px; border-radius: 3px; background: ${info.corTexto}; border: 1px solid #475569;"></span>${info.corTexto}</span>
                        <span style="color: #94a3b8;">Radius:</span><span>${info.borderRadius}</span>
                        <span style="color: #94a3b8;">Fonte:</span><span>${info.fonte} ${info.tamanhoFonte} (${info.pesoFonte})</span>
                    </div>
                </div>

                <div style="margin-bottom: 16px;">
                    <div style="color: #94a3b8; font-size: 11px; text-transform: uppercase; margin-bottom: 6px;">Hierarquia</div>
                    <code style="display: block; background: #0f172a; padding: 8px; border-radius: 6px; font-size: 11px; color: #94a3b8;">${info.hierarquia}</code>
                </div>

                <button onclick="copiarTudo()" style="width: 100%; background: ${CORES.destaque}; border: none; color: white; padding: 12px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600;">📋 COPIAR TUDO</button>
            </div>
        `;

        window._inspetorInfo = info;

        let posX = x + 10;
        let posY = y + 10;

        if (posX + 420 > window.innerWidth) posX = x - 430;
        if (posY + 500 > window.innerHeight) posY = window.innerHeight - 520;
        if (posY < 10) posY = 10;

        popup.style.left = posX + 'px';
        popup.style.top = posY + 'px';
        popup.style.display = 'block';
    }

    window.copiarTudo = function() {
        const info = window._inspetorInfo;
        if (!info) return;

        const conteudoTexto = info.conteudo && info.conteudo !== '-' ? ` | Conteudo: "${info.conteudo}"` : '';
        const eventosTexto = info.eventos && info.eventos !== 'nenhum' ? ` | Eventos: ${info.eventos}` : '';
        const funcaoTexto = funcaoCapturada ? ` | FUNCAO CAPTURADA: ${funcaoCapturada.funcao} (${funcaoCapturada.tipo || 'clique'} em ${funcaoCapturada.seletor})` : '';
        const texto = `Tela: ${info.telaAtiva} | Elemento: ${info.seletor}${conteudoTexto}${funcaoTexto}${eventosTexto} (${info.largura}x${info.altura}, bg: ${info.background}, radius: ${info.borderRadius}, padding: ${info.padding}, margin: ${info.margin}, cor: ${info.corTexto}, fonte: ${info.tamanhoFonte} ${info.pesoFonte}, posicao: esq=${info.distEsquerda} dir=${info.distDireita} topo=${info.distTopo} baixo=${info.distBaixo})`;

        navigator.clipboard.writeText(texto).then(() => {
            showToast('📋 Informacoes copiadas!');
        }).catch(() => {
            const ta = document.createElement('textarea');
            ta.value = texto;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            showToast('📋 Informacoes copiadas!');
        });
    };

    function showToast(msg) {
        let toast = document.getElementById('inspetor-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'inspetor-toast';
            toast.style.cssText = `
                position: fixed;
                bottom: 80px;
                right: 20px;
                z-index: 99999;
                background: ${CORES.fundo};
                color: ${CORES.texto};
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 13px;
                font-family: Montserrat, system-ui, sans-serif;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                opacity: 0;
                transition: opacity 0.3s ease;
            `;
            document.body.appendChild(toast);
        }

        toast.textContent = msg;
        toast.style.opacity = '1';

        setTimeout(() => {
            toast.style.opacity = '0';
        }, 2500);
    }

    // Inicializar com detecção automática
    function init() {
        detectarEInicializar();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
