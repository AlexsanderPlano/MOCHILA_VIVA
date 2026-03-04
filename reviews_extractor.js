// ============================================================
// EXTRATOR DE DATAS DE REVIEWS - Mercado Livre
// ============================================================
//
// COMO USAR:
// 1. Va para a busca do ML filtrada pelo vendedor, ex:
//    https://lista.mercadolivre.com.br/mochila-pirulito_Loja_claudinhodosom-rj
//    OU va na loja do vendedor e busque "mochila pirulito"
// 2. Role ate o final para carregar todos os produtos
// 3. Abra Console (F12 > Console)
// 4. Cole este script INTEIRO e pressione Enter
// 5. Aguarde... leva ~3s por produto
//
// RESULTADO: Tabela com datas de reviews + JSON copiado pro clipboard
// ============================================================

(async function() {
    const DELAY_MS = 3000; // espera entre requests (evitar bloqueio)

    console.log('=============================================');
    console.log('  EXTRATOR DE DATAS DE REVIEWS - ML');
    console.log('=============================================\n');

    // ---- PASSO 1: Coletar MLB IDs da pagina ----
    const allLinks = document.querySelectorAll('a[href*="MLB"]');
    const produtos = new Map();

    allLinks.forEach(link => {
        const match = link.href.match(/MLB-?(\d+)/);
        if (!match) return;
        const mlbId = match[1];
        if (produtos.has(mlbId)) return;

        const card = link.closest('.ui-search-layout__item, .poly-card, .ui-search-result');
        let titulo = '';
        let reviews = '0';
        let rating = '';

        if (card) {
            const titleEl = card.querySelector(
                '.ui-search-item__title, .poly-component__title a, .poly-card__content a, a[class*="title"]'
            );
            titulo = titleEl ? titleEl.textContent.trim() : '';

            const revEl = card.querySelector('.ui-search-reviews__amount, .poly-reviews__total');
            reviews = revEl ? revEl.textContent.trim().replace(/[()]/g, '') : '0';

            const ratEl = card.querySelector('.ui-search-reviews__rating-number, .poly-reviews__rating');
            rating = ratEl ? ratEl.textContent.trim() : '';
        }
        if (!titulo) titulo = link.textContent.trim().substring(0, 80) || mlbId;

        produtos.set(mlbId, {
            mlbId: 'MLB' + mlbId,
            titulo,
            reviews,
            rating,
            url: link.href
        });
    });

    console.log(`Encontrados ${produtos.size} produtos unicos\n`);

    if (produtos.size === 0) {
        console.log('Nenhum produto encontrado!');
        console.log('Verifique se esta na pagina de listagem do vendedor.');
        console.log('Os cards de produto devem estar visiveis na tela.');
        return;
    }

    // ---- PASSO 2: Buscar cada produto e extrair datas ----
    const resultados = [];
    let idx = 0;

    for (const [mlbId, prod] of produtos) {
        idx++;
        const label = prod.titulo.substring(0, 55);
        console.log(`[${idx}/${produtos.size}] ${label}...`);

        const resultado = {
            mlbId: prod.mlbId,
            titulo: prod.titulo,
            reviewsVisiveis: prod.reviews,
            rating: prod.rating,
            url: prod.url,
            datasCriacao: null,
            reviewMaisAntigo: null,
            reviewMaisRecente: null,
            totalDatasEncontradas: 0,
            todasDatas: [],
            metodo: '',
            erro: null
        };

        try {
            const resp = await fetch(prod.url, {
                credentials: 'include',
                headers: {
                    'Accept': 'text/html,application/xhtml+xml',
                    'Accept-Language': 'pt-BR,pt;q=0.9'
                }
            });

            if (!resp.ok) {
                resultado.erro = `HTTP ${resp.status}`;
                resultados.push(resultado);
                continue;
            }

            const html = await resp.text();

            // --- Estrategia 1: __NEXT_DATA__ (Next.js) ---
            const nextDataMatch = html.match(/<script\s+id="__NEXT_DATA__"[^>]*>([\s\S]*?)<\/script>/);
            if (nextDataMatch) {
                try {
                    const nextData = JSON.parse(nextDataMatch[1]);
                    const jsonStr = JSON.stringify(nextData);

                    // Procurar date_created do item
                    const dcMatch = jsonStr.match(/"date_created"\s*:\s*"([^"]+)"/);
                    if (dcMatch) resultado.datasCriacao = dcMatch[1];

                    // Procurar datas de reviews
                    const reviewDates = [];
                    const rdRegex = /"datePublished"\s*:\s*"([^"]+)"/g;
                    let m;
                    while ((m = rdRegex.exec(jsonStr)) !== null) reviewDates.push(m[1]);

                    const rdRegex2 = /"date_created"\s*:\s*"(\d{4}-\d{2}-\d{2}T[^"]+)"/g;
                    while ((m = rdRegex2.exec(jsonStr)) !== null) {
                        if (!reviewDates.includes(m[1])) reviewDates.push(m[1]);
                    }

                    if (reviewDates.length > 0) {
                        reviewDates.sort();
                        resultado.reviewMaisAntigo = reviewDates[0];
                        resultado.reviewMaisRecente = reviewDates[reviewDates.length - 1];
                        resultado.totalDatasEncontradas = reviewDates.length;
                        resultado.todasDatas = reviewDates;
                        resultado.metodo = '__NEXT_DATA__';
                    }
                } catch (e) {
                    // JSON parse falhou, tentar proximo metodo
                }
            }

            // --- Estrategia 2: JSON-LD (structured data) ---
            if (resultado.totalDatasEncontradas === 0) {
                const ldMatches = html.matchAll(/<script\s+type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g);
                for (const ldMatch of ldMatches) {
                    try {
                        const ld = JSON.parse(ldMatch[1]);
                        const ldStr = JSON.stringify(ld);

                        const reviewDates = [];
                        const dpRegex = /"datePublished"\s*:\s*"([^"]+)"/g;
                        let m;
                        while ((m = dpRegex.exec(ldStr)) !== null) reviewDates.push(m[1]);

                        if (reviewDates.length > 0) {
                            reviewDates.sort();
                            resultado.reviewMaisAntigo = reviewDates[0];
                            resultado.reviewMaisRecente = reviewDates[reviewDates.length - 1];
                            resultado.totalDatasEncontradas = reviewDates.length;
                            resultado.todasDatas = reviewDates;
                            resultado.metodo = 'JSON-LD';
                        }
                    } catch (e) { }
                }
            }

            // --- Estrategia 3: Regex no HTML bruto ---
            if (resultado.totalDatasEncontradas === 0) {
                const datas = [];

                // Formato "21 jul. 2017" ou "03 abr. 2025"
                const brRegex = /(\d{1,2})\s+(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\.?\s+(\d{4})/gi;
                let m;
                while ((m = brRegex.exec(html)) !== null) {
                    const mesMap = {jan:'01',fev:'02',mar:'03',abr:'04',mai:'05',jun:'06',jul:'07',ago:'08',set:'09',out:'10',nov:'11',dez:'12'};
                    const mes = mesMap[m[2].toLowerCase()];
                    if (mes) {
                        const iso = `${m[3]}-${mes}-${m[1].padStart(2,'0')}`;
                        datas.push(iso);
                    }
                }

                // Formato espanhol "21 jul. 2017"
                const esRegex = /(\d{1,2})\s+(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\.?\s+(\d{4})/gi;
                while ((m = esRegex.exec(html)) !== null) {
                    const mesMap = {ene:'01',feb:'02',mar:'03',abr:'04',may:'05',jun:'06',jul:'07',ago:'08',sep:'09',oct:'10',nov:'11',dic:'12'};
                    const mes = mesMap[m[2].toLowerCase()];
                    if (mes) {
                        const iso = `${m[3]}-${mes}-${m[1].padStart(2,'0')}`;
                        if (!datas.includes(iso)) datas.push(iso);
                    }
                }

                // Formato ISO em JSON
                const isoRegex = /"(\d{4}-\d{2}-\d{2})T\d{2}:\d{2}/g;
                while ((m = isoRegex.exec(html)) !== null) {
                    if (!datas.includes(m[1])) datas.push(m[1]);
                }

                if (datas.length > 0) {
                    datas.sort();
                    resultado.reviewMaisAntigo = datas[0];
                    resultado.reviewMaisRecente = datas[datas.length - 1];
                    resultado.totalDatasEncontradas = datas.length;
                    resultado.todasDatas = datas;
                    resultado.metodo = 'HTML-regex';
                }
            }

            // --- Estrategia 4: Buscar start_time / date_created do item no HTML ---
            if (!resultado.datasCriacao) {
                const stMatch = html.match(/"start_time"\s*:\s*"([^"]+)"/);
                if (stMatch) resultado.datasCriacao = stMatch[1];
            }

            if (resultado.totalDatasEncontradas > 0) {
                console.log(`  -> ${resultado.totalDatasEncontradas} datas (${resultado.metodo}): ${resultado.reviewMaisAntigo} ate ${resultado.reviewMaisRecente}`);
            } else if (resultado.datasCriacao) {
                console.log(`  -> Sem datas de reviews, mas item criado em: ${resultado.datasCriacao}`);
            } else {
                console.log(`  -> Nenhuma data encontrada`);
            }

        } catch (e) {
            resultado.erro = e.message;
            console.warn(`  -> ERRO: ${e.message}`);
        }

        resultados.push(resultado);

        // Rate limit
        if (idx < produtos.size) {
            await new Promise(r => setTimeout(r, DELAY_MS));
        }
    }

    // ---- PASSO 3: Resumo ----
    console.log('\n=============================================');
    console.log('  RESULTADOS FINAIS');
    console.log('=============================================\n');

    console.table(resultados.map(r => ({
        'MLB': r.mlbId,
        'Titulo': r.titulo.substring(0, 45),
        'Reviews': r.reviewsVisiveis,
        'Rating': r.rating,
        'Datas': r.totalDatasEncontradas,
        'Mais Antigo': r.reviewMaisAntigo || '-',
        'Mais Recente': r.reviewMaisRecente || '-',
        'Criacao Item': r.datasCriacao ? r.datasCriacao.substring(0, 10) : '-',
        'Metodo': r.metodo || (r.erro ? 'ERRO' : 'nada')
    })));

    // Resumo geral
    const comDatas = resultados.filter(r => r.totalDatasEncontradas > 0);
    const semDatas = resultados.filter(r => r.totalDatasEncontradas === 0);
    const todasDatasGlobal = resultados.flatMap(r => r.todasDatas).sort();

    console.log(`\n--- RESUMO DO VENDEDOR ---`);
    console.log(`Produtos analisados: ${resultados.length}`);
    console.log(`Com datas de reviews: ${comDatas.length}`);
    console.log(`Sem datas de reviews: ${semDatas.length}`);
    if (todasDatasGlobal.length > 0) {
        console.log(`Data MAIS ANTIGA (global): ${todasDatasGlobal[0]}`);
        console.log(`Data MAIS RECENTE (global): ${todasDatasGlobal[todasDatasGlobal.length - 1]}`);
    }

    // Copiar para clipboard
    const output = {
        vendedor: document.title,
        dataExtracao: new Date().toISOString(),
        totalProdutos: resultados.length,
        comDatasReviews: comDatas.length,
        dataMaisAntigaGlobal: todasDatasGlobal[0] || null,
        dataMaisRecenteGlobal: todasDatasGlobal[todasDatasGlobal.length - 1] || null,
        produtos: resultados
    };

    const json = JSON.stringify(output, null, 2);

    try {
        await navigator.clipboard.writeText(json);
        console.log('\nResultados copiados para o clipboard!');
    } catch (e) {
        // Fallback: download
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'reviews_' + Date.now() + '.json';
        a.click();
        URL.revokeObjectURL(url);
        console.log('\nArquivo JSON baixado automaticamente!');
    }

    window._reviewResults = output;
    console.log('Dados salvos em window._reviewResults');
    console.log('\n--- Se nenhuma data de review foi encontrada ---');
    console.log('O ML renderiza reviews via JavaScript (nao esta no HTML inicial).');
    console.log('Nesse caso, use o SCRIPT 2 (reviews_manual.js) em cada produto.');
})();
