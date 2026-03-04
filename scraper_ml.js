// ============================================================
// SCRAPER MERCADO LIVRE - Mochila Pirulito
// ============================================================
// 1. Abra https://lista.mercadolivre.com.br/mochila-pirulito
// 2. Role até o final da página para carregar todos os produtos
// 3. Abra o Console (F12 > Console)
// 4. Cole este código e pressione Enter
// 5. Repita para cada página (mude a URL para _Desde_49, _Desde_97, etc)
//    Ou use o botão "Próxima" e rode novamente
// 6. No final, rode: copiarTudo() para copiar o JSON completo
// ============================================================

// Armazena todos os resultados (acumula entre páginas)
if (!window._mlResultados) window._mlResultados = [];

(function() {
    const produtos = [];

    // Selecionar todos os cards de produto
    const cards = document.querySelectorAll('.ui-search-layout__item');

    cards.forEach((card, idx) => {
        try {
            // Título
            const tituloEl = card.querySelector('.ui-search-item__title, .poly-component__title a, .poly-card__content a');
            const titulo = tituloEl ? tituloEl.textContent.trim() : '';

            // Link
            const linkEl = card.querySelector('a.ui-search-link, a.poly-component__title, .poly-card__content a, a[href*="produto.mercadolivre"]');
            const link = linkEl ? linkEl.href : '';

            // Preço
            const precoEl = card.querySelector('.andes-money-amount__fraction, .poly-price__current .andes-money-amount__fraction');
            const centEl = card.querySelector('.andes-money-amount__cents');
            let preco = precoEl ? precoEl.textContent.replace(/\./g, '') : '0';
            if (centEl) preco += '.' + centEl.textContent;

            // Preço original (riscado)
            const precoOrigEl = card.querySelector('.andes-money-amount--previous .andes-money-amount__fraction');
            const precoOrig = precoOrigEl ? precoOrigEl.textContent.replace(/\./g, '') : '';

            // Vendedor
            const vendedorEl = card.querySelector('.poly-component__seller, .ui-search-official-store-label, .ui-search-item__group__element--seller');
            const vendedor = vendedorEl ? vendedorEl.textContent.trim() : '';

            // Vendas
            const vendasEl = card.querySelector('.ui-search-reviews__amount, .poly-reviews__total');
            let vendas = '';
            // Tentar pegar vendas do texto
            const textos = card.querySelectorAll('span');
            textos.forEach(span => {
                const t = span.textContent.trim().toLowerCase();
                if (t.includes('vendido') || t.includes('vendas')) {
                    vendas = t;
                }
            });

            // Rating
            const ratingEl = card.querySelector('.ui-search-reviews__rating-number, .poly-reviews__rating');
            const rating = ratingEl ? ratingEl.textContent.trim() : '';

            // Reviews count
            const reviewsEl = card.querySelector('.ui-search-reviews__amount, .poly-reviews__total');
            const reviews = reviewsEl ? reviewsEl.textContent.trim().replace(/[()]/g, '') : '';

            // Frete grátis
            const freteEl = card.querySelector('.ui-search-item__shipping--free, .poly-component__shipping');
            let freteGratis = false;
            if (freteEl) {
                freteGratis = freteEl.textContent.toLowerCase().includes('grátis') ||
                              freteEl.textContent.toLowerCase().includes('gratis');
            }

            // Full (Mercado Envios Full)
            const fullEl = card.querySelector('.ui-search-item__fulfillment, [class*="full"]');
            const isFull = fullEl ? fullEl.textContent.toLowerCase().includes('full') : false;

            // Tipo de anúncio (patrocinado)
            const patrocinadoEl = card.querySelector('.ui-search-item__pub-label, .poly-component__ad-label');
            const patrocinado = patrocinadoEl ? true : false;

            // Localização
            const localEl = card.querySelector('.ui-search-item__location, .poly-component__location');
            const local = localEl ? localEl.textContent.trim() : '';

            // Extrair item ID do link
            let itemId = '';
            if (link) {
                const match = link.match(/MLB-?\d+/);
                if (match) itemId = match[0];
            }

            if (titulo) {
                produtos.push({
                    pagina: window._mlPaginaAtual || 1,
                    posicao: idx + 1,
                    itemId,
                    titulo,
                    preco: parseFloat(preco) || 0,
                    precoOriginal: precoOrig ? parseFloat(precoOrig) : null,
                    vendedor,
                    vendas,
                    rating,
                    reviews,
                    freteGratis,
                    full: isFull,
                    patrocinado,
                    local,
                    link
                });
            }
        } catch (e) {
            console.warn(`Erro no card ${idx}:`, e);
        }
    });

    // Adicionar ao acumulador global
    window._mlResultados.push(...produtos);

    // Incrementar página
    if (!window._mlPaginaAtual) window._mlPaginaAtual = 1;
    window._mlPaginaAtual++;

    // Resumo
    console.log(`\n========================================`);
    console.log(`PÁGINA ${window._mlPaginaAtual - 1}: ${produtos.length} produtos encontrados`);
    console.log(`TOTAL ACUMULADO: ${window._mlResultados.length} produtos`);
    console.log(`========================================`);

    // Tabela resumida
    console.table(produtos.map(p => ({
        '#': p.posicao,
        Titulo: p.titulo.substring(0, 60) + (p.titulo.length > 60 ? '...' : ''),
        Preco: `R$ ${p.preco.toFixed(2)}`,
        Vendedor: p.vendedor.substring(0, 25),
        Rating: p.rating,
        Frete: p.freteGratis ? 'GRÁTIS' : '-',
        Patrocinado: p.patrocinado ? 'SIM' : '-'
    })));

    console.log(`\nPróximo passo:`);
    console.log(`  - Vá para a próxima página e rode este script novamente`);
    console.log(`  - Quando terminar TODAS as páginas, rode: copiarTudo()`);
})();

// Função para copiar tudo ao clipboard
window.copiarTudo = function() {
    const json = JSON.stringify(window._mlResultados, null, 2);
    navigator.clipboard.writeText(json).then(() => {
        console.log(`\n✅ ${window._mlResultados.length} produtos copiados para o clipboard!`);
        console.log(`Cole em um arquivo .json e me envie.`);
    }).catch(() => {
        // Fallback: criar download
        const blob = new Blob([json], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'mochila_pirulito_ml.json';
        a.click();
        console.log(`\n✅ Arquivo baixado: mochila_pirulito_ml.json`);
    });
};

// Função para resetar (se quiser recomeçar)
window.resetarML = function() {
    window._mlResultados = [];
    window._mlPaginaAtual = 1;
    console.log('Resultados resetados.');
};
