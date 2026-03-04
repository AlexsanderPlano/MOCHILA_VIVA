// ============================================================
// EXTRATOR DE REVIEWS - Modo Manual (SCRIPT 2)
// ============================================================
//
// USE ESTE SCRIPT quando o Script 1 (reviews_extractor.js) nao
// encontrar datas de reviews (ML renderiza via JavaScript).
//
// COMO USAR:
// 1. Abra a pagina de um PRODUTO especifico no ML
// 2. Role ate a secao "Opinioes sobre o produto"
// 3. Clique em "Ver todas as opinioes" se disponivel
// 4. Abra Console (F12 > Console)
// 5. Cole este script e pressione Enter
// 6. O script vai rolar automaticamente para carregar todos os reviews
// 7. Resultado: lista de datas + mais antiga + mais recente
//
// ============================================================

(async function() {
    console.log('=============================================');
    console.log('  EXTRATOR DE REVIEWS - Modo Manual');
    console.log('=============================================\n');

    // Detectar se esta na pagina certa
    const url = window.location.href;
    const mlbMatch = url.match(/MLB-?(\d+)/);
    const mlbId = mlbMatch ? 'MLB' + mlbMatch[1] : 'desconhecido';
    console.log(`Produto: ${mlbId}`);
    console.log(`URL: ${url}\n`);

    // Funcao para rolar e carregar mais reviews
    async function carregarTodosReviews() {
        const reviewSection = document.querySelector(
            '.ui-review-capability, [class*="reviews"], [class*="opiniones"]'
        );

        if (!reviewSection) {
            console.log('Secao de reviews nao encontrada na pagina.');
            console.log('Tente rolar ate a secao de opiniones/reviews primeiro.');
            return false;
        }

        // Clicar em "Ver mais" ate nao ter mais
        let tentativas = 0;
        while (tentativas < 50) {
            const verMaisBtn = document.querySelector(
                'button[class*="show-more"], button[class*="ver-mais"], ' +
                '.ui-review-capability__action--secondary, ' +
                '[class*="reviews"] button:not([disabled]), ' +
                'button[data-testid*="more"]'
            );

            if (!verMaisBtn || verMaisBtn.disabled) break;

            verMaisBtn.click();
            tentativas++;
            console.log(`  Carregando mais reviews... (${tentativas})`);
            await new Promise(r => setTimeout(r, 1500));
        }

        return true;
    }

    // Tentar carregar todos os reviews
    await carregarTodosReviews();

    // Esperar um pouco para o DOM atualizar
    await new Promise(r => setTimeout(r, 2000));

    // Extrair datas de reviews do DOM renderizado
    const datas = [];

    // Seletores comuns para datas de review no ML
    const seletoresData = [
        '.ui-review-capability-comments__comment__date',
        '[class*="review"] [class*="date"]',
        '[class*="review"] time',
        '[class*="opinion"] [class*="date"]',
        '[class*="opinion"] time',
        '.ui-review-view__comment__date',
        'time[datetime]',
        'span[class*="date"]',
        'p[class*="date"]'
    ];

    // Tentar cada seletor
    for (const seletor of seletoresData) {
        const els = document.querySelectorAll(seletor);
        els.forEach(el => {
            // Tentar atributo datetime primeiro
            let dateStr = el.getAttribute('datetime') || el.textContent.trim();
            if (dateStr && dateStr.length > 4) {
                datas.push(dateStr);
            }
        });
    }

    // Tambem procurar no texto da pagina por padroes de data
    if (datas.length === 0) {
        console.log('\nSeletores diretos nao encontraram datas.');
        console.log('Procurando por padroes de data no texto...\n');

        // Pegar todo texto visivel na area de reviews
        const reviewContainers = document.querySelectorAll(
            '[class*="review"], [class*="opinion"], [class*="comment"]'
        );

        reviewContainers.forEach(container => {
            const texto = container.textContent;

            // Formato brasileiro: "21 jul. 2017"
            const brRegex = /(\d{1,2})\s+(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\.?\s+(\d{4})/gi;
            let m;
            while ((m = brRegex.exec(texto)) !== null) {
                datas.push(m[0]);
            }

            // Formato espanhol: "21 jul. 2017"
            const esRegex = /(\d{1,2})\s+(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\.?\s+(\d{4})/gi;
            while ((m = esRegex.exec(texto)) !== null) {
                if (!datas.includes(m[0])) datas.push(m[0]);
            }

            // Formato dd/mm/yyyy
            const slashRegex = /(\d{2})\/(\d{2})\/(\d{4})/g;
            while ((m = slashRegex.exec(texto)) !== null) {
                datas.push(m[0]);
            }
        });
    }

    // Converter e ordenar
    const mesMap = {
        jan:'01',fev:'02',mar:'03',abr:'04',mai:'05',jun:'06',
        jul:'07',ago:'08',set:'09',out:'10',nov:'11',dez:'12',
        ene:'01',feb:'02',abr:'04',may:'05',ago:'08',
        sep:'09',oct:'10',dic:'12'
    };

    const datasISO = datas.map(d => {
        // Ja e ISO?
        if (/^\d{4}-\d{2}-\d{2}/.test(d)) return d.substring(0, 10);

        // Formato "21 jul. 2017"
        const brMatch = d.match(/(\d{1,2})\s+(\w{3})\.?\s+(\d{4})/);
        if (brMatch) {
            const mes = mesMap[brMatch[2].toLowerCase()];
            if (mes) return `${brMatch[3]}-${mes}-${brMatch[1].padStart(2, '0')}`;
        }

        // Formato dd/mm/yyyy
        const slashMatch = d.match(/(\d{2})\/(\d{2})\/(\d{4})/);
        if (slashMatch) return `${slashMatch[3]}-${slashMatch[2]}-${slashMatch[1]}`;

        return d;
    }).filter(d => /^\d{4}-\d{2}/.test(d));

    // Remover duplicatas e ordenar
    const datasUnicas = [...new Set(datasISO)].sort();

    // Resultado
    console.log('\n=============================================');
    console.log('  RESULTADO');
    console.log('=============================================\n');

    if (datasUnicas.length === 0) {
        console.log('Nenhuma data de review encontrada.');
        console.log('\nPossiveis causas:');
        console.log('1. O produto nao tem reviews');
        console.log('2. Os reviews nao estao carregados (role ate eles)');
        console.log('3. O ML mudou a estrutura do DOM');
        console.log('\nTente manualmente:');
        console.log('1. Role ate "Opinioes sobre o produto"');
        console.log('2. Clique "Ver todas as opinioes"');
        console.log('3. Ordene por "Mais antigas primeiro"');
        console.log('4. Anote a data do PRIMEIRO review visivel');
        console.log('5. Ordene por "Mais recentes primeiro"');
        console.log('6. Anote a data do PRIMEIRO review visivel');
    } else {
        console.log(`Produto: ${mlbId}`);
        console.log(`Total de datas encontradas: ${datasUnicas.length}`);
        console.log(`\n  REVIEW MAIS ANTIGO:  ${datasUnicas[0]}`);
        console.log(`  REVIEW MAIS RECENTE: ${datasUnicas[datasUnicas.length - 1]}`);
        console.log('\nTodas as datas:');
        console.table(datasUnicas.map((d, i) => ({ '#': i + 1, data: d })));

        // Salvar resultado
        const resultado = {
            mlbId,
            url,
            totalDatas: datasUnicas.length,
            maisAntigo: datasUnicas[0],
            maisRecente: datasUnicas[datasUnicas.length - 1],
            todasDatas: datasUnicas,
            extraidoEm: new Date().toISOString()
        };

        // Acumular resultados se ja existirem
        if (!window._reviewsManuais) window._reviewsManuais = [];
        window._reviewsManuais.push(resultado);

        try {
            await navigator.clipboard.writeText(JSON.stringify(resultado, null, 2));
            console.log('\nResultado copiado para o clipboard!');
        } catch (e) {
            console.log('\nCopie manualmente: JSON.stringify(window._reviewsManuais)');
        }

        console.log(`\nAcumulados: ${window._reviewsManuais.length} produtos`);
        console.log('Para ver todos: console.table(window._reviewsManuais)');
        console.log('Para copiar tudo: copy(JSON.stringify(window._reviewsManuais, null, 2))');
    }
})();
