// ============================================================
// EXTRATOR AUTOMATICO DE DATAS - Mercado Livre
// ============================================================
//
// COMO USAR:
// 1. Va para a loja do vendedor no ML, ex:
//    https://lista.mercadolivre.com.br/pagina/claudinhodosomrj/
//    Ou qualquer pagina de listagem com produtos do vendedor
// 2. Role ate o FINAL para carregar todos os produtos
//    (se tiver paginacao, rode em cada pagina)
// 3. Abra Console (F12 > Console)
// 4. Cole este script e pressione Enter
// 5. NAO FECHE A ABA - aguarde todos os produtos serem analisados
//    (~3s por produto = ~3 min para 62 produtos)
// 6. No final, o JSON e copiado pro clipboard automaticamente
//
// ============================================================

(async function() {
    const DELAY = 2500;
    const MAX_TENTATIVAS_PAGINA = 3;

    console.log('%c EXTRATOR AUTOMATICO DE DATAS ML ', 'background:#0a0a23;color:#00ff88;font-size:16px;padding:8px');
    console.log('Coletando links dos produtos na pagina...\n');

    // ---- PASSO 1: Coletar TODOS os links de produtos ----
    const todosLinks = document.querySelectorAll('a[href*="MLB"], a[href*="mercadolivre.com.br/MLB"]');
    const produtosMap = new Map();

    todosLinks.forEach(link => {
        const href = link.href || '';
        const match = href.match(/MLB-?(\d+)/);
        if (!match) return;
        const mlbId = match[1];
        if (produtosMap.has(mlbId)) return;

        // Pegar titulo e reviews do card
        const card = link.closest(
            '.ui-search-layout__item, .poly-card, .ui-search-result, ' +
            '.shops__layout-item, .ui-search-layout--grid__item, li, article'
        );

        let titulo = '', reviews = '0', rating = '';

        if (card) {
            const tEls = card.querySelectorAll('a, h2, h3, span, p');
            for (const el of tEls) {
                const t = el.textContent.trim();
                if (t.length > 15 && t.length < 200 && !t.includes('R$') && !titulo) {
                    titulo = t;
                }
            }
            const revEl = card.querySelector('[class*="reviews__amount"], [class*="reviews__total"]');
            if (revEl) reviews = revEl.textContent.trim().replace(/[()]/g, '');

            const ratEl = card.querySelector('[class*="rating"]');
            if (ratEl) rating = ratEl.textContent.trim();
        }

        if (!titulo) titulo = 'MLB' + mlbId;

        produtosMap.set(mlbId, { mlbId, titulo, reviews, rating, url: href });
    });

    const produtos = Array.from(produtosMap.values());
    console.log(`${produtos.length} produtos unicos encontrados`);

    if (produtos.length === 0) {
        console.log('%c ERRO: Nenhum produto encontrado!', 'color:red;font-weight:bold');
        console.log('Tente:');
        console.log('1. Verifique se esta na pagina da loja do vendedor');
        console.log('2. Role ate o final para carregar todos os cards');
        console.log('3. Tente: document.querySelectorAll("a[href*=MLB]").length');
        return;
    }

    const tempoEstimado = Math.ceil(produtos.length * DELAY / 1000 / 60);
    console.log(`Tempo estimado: ~${tempoEstimado} minutos\n`);
    console.log('Iniciando varredura...\n');

    // ---- PASSO 2: Analisar cada produto via fetch ----
    const resultados = [];
    let comDatas = 0;

    for (let i = 0; i < produtos.length; i++) {
        const prod = produtos[i];
        const progresso = `[${i + 1}/${produtos.length}]`;
        const tituloShort = prod.titulo.substring(0, 50);

        let melhorResultado = {
            mlbId: 'MLB' + prod.mlbId,
            titulo: prod.titulo,
            reviews: prod.reviews,
            rating: prod.rating,
            dataCriacaoItem: null,
            reviewMaisAntigo: null,
            reviewMaisRecente: null,
            qtdDatasEncontradas: 0,
            todasDatas: [],
            metodo: 'nenhum',
            url: prod.url
        };

        for (let tent = 0; tent < MAX_TENTATIVAS_PAGINA; tent++) {
            try {
                const resp = await fetch(prod.url, {
                    credentials: 'include',
                    headers: { 'Accept': 'text/html' }
                });

                if (!resp.ok) {
                    if (resp.status === 429) {
                        console.log(`${progresso} Rate limit! Esperando 10s...`);
                        await new Promise(r => setTimeout(r, 10000));
                        continue;
                    }
                    console.log(`${progresso} HTTP ${resp.status} - ${tituloShort}`);
                    break;
                }

                const html = await resp.text();
                const todasDatas = [];
                let metodo = '';

                // ----- Extrair do __NEXT_DATA__ -----
                const ndMatch = html.match(/<script\s+id="__NEXT_DATA__"[^>]*>([\s\S]*?)<\/script>/);
                if (ndMatch) {
                    try {
                        const nd = JSON.parse(ndMatch[1]);
                        const s = JSON.stringify(nd);

                        // date_created do item
                        const dcM = s.match(/"date_created"\s*:\s*"([^"]+)"/);
                        if (dcM) melhorResultado.dataCriacaoItem = dcM[1].substring(0, 10);

                        // start_time do item
                        if (!melhorResultado.dataCriacaoItem) {
                            const stM = s.match(/"start_time"\s*:\s*"([^"]+)"/);
                            if (stM) melhorResultado.dataCriacaoItem = stM[1].substring(0, 10);
                        }

                        // Reviews com datePublished
                        const dpR = /"datePublished"\s*:\s*"([^"]+)"/g;
                        let m;
                        while ((m = dpR.exec(s)) !== null) {
                            const d = m[1].substring(0, 10);
                            if (/^\d{4}-\d{2}-\d{2}$/.test(d) && !todasDatas.includes(d)) {
                                todasDatas.push(d);
                            }
                        }
                        if (todasDatas.length > 0) metodo = 'NEXT_DATA';
                    } catch (e) { }
                }

                // ----- Extrair de JSON-LD -----
                if (todasDatas.length === 0) {
                    const ldBlocks = html.matchAll(/<script[^>]+type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g);
                    for (const block of ldBlocks) {
                        try {
                            const s = block[1];
                            const dpR = /"datePublished"\s*:\s*"([^"]+)"/g;
                            let m;
                            while ((m = dpR.exec(s)) !== null) {
                                const d = m[1].substring(0, 10);
                                if (/^\d{4}-\d{2}-\d{2}$/.test(d) && !todasDatas.includes(d)) {
                                    todasDatas.push(d);
                                }
                            }
                            if (todasDatas.length > 0) metodo = 'JSON-LD';
                        } catch (e) { }
                    }
                }

                // ----- Extrair datas do HTML bruto (regex) -----
                if (todasDatas.length === 0) {
                    const mesMapBR = { jan: '01', fev: '02', mar: '03', abr: '04', mai: '05', jun: '06', jul: '07', ago: '08', set: '09', out: '10', nov: '11', dez: '12' };
                    const mesMapES = { ene: '01', feb: '02', mar: '03', abr: '04', may: '05', jun: '06', jul: '07', ago: '08', sep: '09', oct: '10', nov: '11', dic: '12' };

                    // PT: "21 jul. 2017"
                    const brR = /(\d{1,2})\s+(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\.?\s+(\d{4})/gi;
                    let m;
                    while ((m = brR.exec(html)) !== null) {
                        const mes = mesMapBR[m[2].toLowerCase()];
                        if (mes) {
                            const d = `${m[3]}-${mes}-${m[1].padStart(2, '0')}`;
                            if (!todasDatas.includes(d)) todasDatas.push(d);
                        }
                    }

                    // ES: "21 jul. 2017"
                    const esR = /(\d{1,2})\s+(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\.?\s+(\d{4})/gi;
                    while ((m = esR.exec(html)) !== null) {
                        const mes = mesMapES[m[2].toLowerCase()];
                        if (mes) {
                            const d = `${m[3]}-${mes}-${m[1].padStart(2, '0')}`;
                            if (!todasDatas.includes(d)) todasDatas.push(d);
                        }
                    }

                    if (todasDatas.length > 0) metodo = 'HTML-regex';
                }

                // ----- Fallback: date_created do item -----
                if (!melhorResultado.dataCriacaoItem) {
                    const dcFallback = html.match(/"(?:date_created|start_time)"\s*:\s*"(\d{4}-\d{2}-\d{2})/);
                    if (dcFallback) melhorResultado.dataCriacaoItem = dcFallback[1];
                }

                // Salvar resultado
                if (todasDatas.length > 0) {
                    todasDatas.sort();
                    melhorResultado.reviewMaisAntigo = todasDatas[0];
                    melhorResultado.reviewMaisRecente = todasDatas[todasDatas.length - 1];
                    melhorResultado.qtdDatasEncontradas = todasDatas.length;
                    melhorResultado.todasDatas = todasDatas;
                    melhorResultado.metodo = metodo;
                    comDatas++;
                }

                break; // sucesso, sair do loop de tentativas

            } catch (e) {
                if (tent === MAX_TENTATIVAS_PAGINA - 1) {
                    console.warn(`${progresso} ERRO final: ${e.message}`);
                } else {
                    await new Promise(r => setTimeout(r, 3000));
                }
            }
        }

        // Log de progresso
        if (melhorResultado.qtdDatasEncontradas > 0) {
            console.log(`%c${progresso} ${tituloShort}  -->  ${melhorResultado.reviewMaisAntigo} ate ${melhorResultado.reviewMaisRecente} (${melhorResultado.qtdDatasEncontradas} datas)`, 'color:#00ff88');
        } else if (melhorResultado.dataCriacaoItem) {
            console.log(`${progresso} ${tituloShort}  -->  sem reviews, item criado: ${melhorResultado.dataCriacaoItem}`);
        } else {
            console.log(`%c${progresso} ${tituloShort}  -->  nada encontrado`, 'color:#ff6666');
        }

        resultados.push(melhorResultado);

        // Rate limit
        if (i < produtos.length - 1) {
            await new Promise(r => setTimeout(r, DELAY));
        }
    }

    // ---- PASSO 3: RESULTADO FINAL ----
    console.log('\n%c RESULTADO FINAL ', 'background:#0a0a23;color:#00ff88;font-size:14px;padding:6px');

    // Tabela resumo
    console.table(resultados.map(r => ({
        MLB: r.mlbId,
        Titulo: r.titulo.substring(0, 40),
        Reviews: r.reviews,
        'Mais Antigo': r.reviewMaisAntigo || r.dataCriacaoItem || '-',
        'Mais Recente': r.reviewMaisRecente || '-',
        '#Datas': r.qtdDatasEncontradas,
        Metodo: r.metodo
    })));

    // Calcular resumo global
    const todosReviewDatas = resultados
        .filter(r => r.qtdDatasEncontradas > 0)
        .flatMap(r => r.todasDatas)
        .sort();

    const todasCriacoes = resultados
        .filter(r => r.dataCriacaoItem)
        .map(r => r.dataCriacaoItem)
        .sort();

    console.log('\n--- RESUMO GLOBAL DO VENDEDOR ---');
    console.log(`Produtos analisados: ${resultados.length}`);
    console.log(`Produtos com datas de reviews: ${comDatas}`);
    console.log(`Produtos com data de criacao: ${todasCriacoes.length}`);

    if (todosReviewDatas.length > 0) {
        console.log(`%cReview MAIS ANTIGO: ${todosReviewDatas[0]}`, 'color:#00ff88;font-size:14px;font-weight:bold');
        console.log(`%cReview MAIS RECENTE: ${todosReviewDatas[todosReviewDatas.length - 1]}`, 'color:#00ff88;font-size:14px;font-weight:bold');
    } else {
        console.log('%cNenhuma data de review encontrada via fetch', 'color:#ff6666');
        console.log('O ML nao inclui datas de reviews no HTML inicial (renderiza via JS).');
        console.log('');
        console.log('ALTERNATIVA: Use as datas de CRIACAO dos itens como proxy:');
        if (todasCriacoes.length > 0) {
            console.log(`  Item mais antigo criado em: ${todasCriacoes[0]}`);
            console.log(`  Item mais recente criado em: ${todasCriacoes[todasCriacoes.length - 1]}`);
        }
    }

    // Salvar e copiar
    const output = {
        vendedor: document.title || window.location.href,
        paginaOrigem: window.location.href,
        dataExtracao: new Date().toISOString(),
        totalProdutos: resultados.length,
        produtosComDatasReviews: comDatas,
        produtosComDataCriacao: todasCriacoes.length,
        reviewMaisAntigoGlobal: todosReviewDatas[0] || null,
        reviewMaisRecenteGlobal: todosReviewDatas[todosReviewDatas.length - 1] || null,
        itemMaisAntigoCriado: todasCriacoes[0] || null,
        itemMaisRecenteCriado: todasCriacoes[todasCriacoes.length - 1] || null,
        produtos: resultados
    };

    const json = JSON.stringify(output, null, 2);

    try {
        await navigator.clipboard.writeText(json);
        console.log('\n%c Resultado copiado para o clipboard! ', 'background:#00ff88;color:#000;padding:4px');
    } catch (e) {
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `reviews_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        console.log('\n Arquivo JSON baixado!');
    }

    window._resultadoFinal = output;
    console.log('Dados em: window._resultadoFinal');
})();
