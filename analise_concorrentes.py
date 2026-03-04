"""
Analise de Concorrentes - Mochila Pirulito no Mercado Livre
============================================================
Dados coletados de 5 paginas de busca "mochila pirulito" em 02/03/2026.
Gera analise completa com:
  - Lista de vendedores com contagem e faixa de preco
  - Distribuicao de precos (preco unitario normalizado)
  - Categorias de produto (unidade, kits, acessorios, nao-relevante)
  - Top vendedores por numero de anuncios
  - Precos medios por vendedor
Salva resultados em analise_concorrentes.xlsx (multiplas abas).
"""

import pandas as pd
import re
import os
from collections import defaultdict

# ---------------------------------------------------------------------------
# 1. RAW DATA - All 5 pages hardcoded
# ---------------------------------------------------------------------------
# Each entry: (page, index_in_page, title, price_brl, seller_raw)
# seller_raw = None when not identified in the listing

RAW_DATA = [
    # ===== PAGE 1 (60 products) =====
    (1, 1, "Mochila Pirulito Eventos Acoes Com 1 Placa Redonda", 135.00, "BALCAO E BANDEJA"),
    (1, 2, "Kit Com 4 Mochila Pirulito, Acoes Promocoes E Eventos", 714.92, None),
    (1, 3, "Mochila Pirulito Eventos 4 Unid Com 8 Placas", 550.58, "MOCHILA PIRULITO"),
    (1, 4, "Mochila Pirulito Propaganda Com 2 Placas Para Personalizar", 135.56, "CLAUDINHO DO SOM"),
    (1, 5, "Mochila Pirulito Caixa Com Placas Personalizada", 134.90, None),
    (1, 6, "Mochilas Divulgacao Pirulito Sem Personalizar", 78.10, "MIDIAS"),
    (1, 7, "Mochilas Divulgacao Pirulito Sem Personalizar", 78.90, "MIDIAS"),
    (1, 8, "Mochila Pirulito Propaganda", 162.50, None),
    (1, 9, "Mochilas Pirulito Sem Personalizar Duas Placas", 78.90, "MIDIAS"),
    (1, 10, "Mochila Pirulito Propaganda Com 2 Placas Para Personalizar", 135.56, "CLAUDINHO DO SOM"),
    (1, 11, "Mochila Pirulito - Mochila Caixa Movel", 162.50, None),
    (1, 12, "Mochila Pirulito Eventos Acoes Com 1 Placa Redonda", 135.00, "BALCAO E BANDEJA"),
    (1, 13, "Mochila Pirulito Eventos Acoes Com 1 Placa", 135.00, "BALCAO E BANDEJA"),
    (1, 14, "Mochila Pirulito Com 2 Placas Sem Impressao Cor Preto", 164.40, "PROPAGANDA PERSONALIZADA"),
    (1, 15, "Mochila Pirulito - Preto Liso (kit Com 05 Unidades) Caixa", 670.80, None),
    (1, 16, "Mochila Pirulito 2 Placas Brancas Frete Gratis E 12x S/juros", 174.62, None),
    (1, 17, "Mochila Pirulito 2 Placas Top, Acoes Promocoes E Eventos", 164.40, "AREAPROMOCIONAL"),
    (1, 18, "Mochila Escolar Com Pirulito De Coracao De Hatsune Miku", 148.22, None),
    (1, 19, "Mochila Pirulito Propaganda 2 Pecas", 289.75, "MOCHILA PIRULITO"),
    (1, 20, "Mochila Pirulito Com 2 Placas Sem Impressao Cor Preto", 164.40, "PROPAGANDA PERSONALIZADA"),
    (1, 21, "Mochila Pirulito - Mochila Caixa Movel (kit Com 02 Unidades)", 309.48, None),
    (1, 22, "Mochila Pirulito - Mochila Caixa Movel (kit Com 10 Unidades)", 1445.78, None),
    (1, 23, "Mochila Pirulito - Mochila Caixa Movel (kit Com 4 Unidades)", 592.45, None),
    (1, 24, "Mochila Pirulito - Mochila Caixa Movel (kit Com 5 Unidades)", 733.50, None),
    (1, 25, "Mochila Pirulito 2 Placas Divulgacao Movel Kit C/ 6 Pcs", 850.50, "CLAUDINHO DO SOM"),
    (1, 26, "Kit Com 10 Mochilas Pirulito Eventos Acoes Com 2 Placas", 1400.90, "BALCAO E BANDEJA"),
    (1, 27, "Mochila Pirulito 2 Placas Top, Acoes Promocoes E Eventos", 164.40, "AREAPROMOCIONAL"),
    (1, 28, "2 Mochilas Pirulito Sem Placas E Sem Haste", 199.17, "MOCHILA PIRULITO"),
    (1, 29, "Mochila Pirulito 2 Placas Brancas Frete Gratis E 12x S/juros", 174.62, None),
    (1, 30, "3 Mochilas Pirulito", 360.90, None),
    (1, 31, "1 Hastes E 2 Placas Para Mochila Pirulito Sem Mochila!!", 93.60, "AREAPROMOCIONAL"),
    (1, 32, "Mochila Pirulito propaganda sem placa com haste de aluminio", 115.25, "CLAUDINHO DO SOM"),
    (1, 33, "Mochila Pirulito - Mochila Eventos", 130.20, None),
    (1, 34, "Mochila Pirulito - Mochila Caixa Movel (kit Com 03 Unidades)", 446.26, None),
    (1, 35, "Mochila Pirulito - Mochila Caixa Movel (kit Com 6 Unidades)", 874.60, None),
    (1, 36, "Mochila Pirulito 2 Placas Divulgacao Movel Kit C/ 6 Pcs", 850.50, "CLAUDINHO DO SOM"),
    (1, 37, "Mochila Pirulito Eventos Acoes Com 1 Placa Quadrada", 135.00, "BALCAO E BANDEJA"),
    (1, 38, "Mochila Pirulito Propaganda Com 2 Placas 38cm Cor Preto", 134.90, None),
    (1, 39, "Mochila Pirulito Eventos 4 Unid Com 8 Placas", 550.58, "MOCHILA PIRULITO"),
    (1, 40, "10 Mochilas Pirulito Duratran Preta Impermeavel 5L Claudinho", 1350.85, "CLAUDINHO DO SOM"),
    (1, 41, "4 Mochilas Pirulito Sem Placas", 440.00, None),
    (1, 42, "Mochila Pirulito Propaganda Divulgacao Movel Kit C/ 2 Pcs", 295.61, "MOCHILA PIRULITO"),
    (1, 43, "Mochila Pirulito Eventos Acoes Com 1 Placa", 135.00, "BALCAO E BANDEJA"),
    (1, 44, "10 Mochilas Pirulito Com 2 Placas Cada", 1350.50, "CLAUDINHO DO SOM"),
    (1, 45, "Mochila Pirulito Propaganda (kit Com 15 Unidades)", 1964.61, None),
    (1, 46, "Mochila Areapromocional Nylon Ziper Preto 40cm Versatil", 164.16, "AREAPROMOCIONAL"),
    (1, 47, "Mochila Pirulito - Preto Liso (kit Com 05 Unidades) Caixa", 670.80, None),
    (1, 48, "6 Mochilas Pirulito com placas de 45cm", 850.50, "MOCHILA PIRULITO"),
    (1, 49, "Mochila Pirulito Com 2 Placas Quadrada 40cm Diametro", 180.19, "PROPAGANDA PERSONALIZADA"),
    (1, 50, "Mochila Pirulito Com Haste+ 2 Placas Brancas E Bolso Lateral", 125.13, "GOBANNERS"),
    (1, 51, "Mochila Pirulito - Mochila Caixa Movel (kit Com 20 Unidades)", 2583.85, None),
    (1, 52, "2 Mochilas Pirulito Sem Placas E Sem Haste", 199.17, "MOCHILA PIRULITO"),
    (1, 53, "Mochila Led Impermeavel Olhos 30l Esportiva Personalizavel", 799.90, "VIRTUAFX"),
    (1, 54, "2 Mochilas Pirulito Sem Placas E Haste", 240.90, None),
    (1, 55, "10 Mochilas Pirulito Sem Placas E Sem A Haste So A Mochila!!", 700.69, "DOUTOR BEER"),
    (1, 56, "Mochila Pirulito Kit Com 6 Pecas", 850.50, "CLAUDINHO DO SOM"),
    (1, 57, "Mochila Pirulito Com 2 Placas Sem Impressao Cor Preto", 175.20, "PROPAGANDA PERSONALIZADA"),
    (1, 58, "Mochila Areapromocional Pirulito Publicidade 2 Placa Branca", 169.20, "AREAPROMOCIONAL"),
    (1, 59, "4 Mochila Pirulito Com 1 Placa Sem Impressao", 648.28, None),
    (1, 60, "Mochilas Propaganda Pirulito Sem Personalizar", 78.90, "MIDIAS"),

    # ===== PAGE 2 (60 products) =====
    (2, 1, "Mochila Pirulito Eventos Acoes Com 1 Placa Redonda", 135.00, "BALCAO E BANDEJA"),
    (2, 2, "Kit Com 4 Mochila Pirulito, Acoes Promocoes E Eventos", 714.92, None),
    (2, 3, "Mochila Pirulito Eventos 4 Unid Com 8 Placas", 550.58, "MOCHILA PIRULITO"),
    (2, 4, "Mochila Pirulito Propaganda Com 2 Placas Para Personalizar", 135.56, "CLAUDINHO DO SOM"),
    (2, 5, "Mochila Pirulito Propaganda - Personalizada", 165.74, None),
    (2, 6, "2 Mochila Pirulito Com 2 Placas Sem Impressao", 357.60, "PROPAGANDA PERSONALIZADA"),
    (2, 7, "Mochila Pirulito Com 2 Placas Quadrada 40cm Personalizada", 252.44, "BALCAO E BANDEJA"),
    (2, 8, "03 Un Mochila Promocional Nylon Ziper Preto 38cm Versatil", 402.90, None),
    (2, 9, "Mochila Pirulito Com 1 Placa Sem Impressao", 174.40, None),
    (2, 10, "Kit Com 2 Mochila Pirulito 2 Placas Brancas Frete Gratis", 405.60, None),
    (2, 11, "5 Mochilas Pirulito Sem Placas E Sem Haste", 490.22, "MOCHILA PIRULITO"),
    (2, 12, "5 Mochilas Pirulito Sem Placas", 550.00, None),
    (2, 13, "Mochila Pirulito Eventos Acoes Com 1 Placa", 135.00, "BALCAO E BANDEJA"),
    (2, 14, "Mochila Pirulito Com 2 Placas Sem Impressao Cor Preto", 164.40, "PROPAGANDA PERSONALIZADA"),
    (2, 15, "Mochila Pirulito - Preto Liso (kit Com 05 Unidades) Caixa", 670.80, None),
    (2, 16, "Mochila Pirulito 2 Placas Brancas Frete Gratis E 12x S/juros", 174.62, None),
    (2, 17, "Mochila Escolar Juvenil Para Costas Pirulito Azul Estampada", 78.99, "DMW"),
    (2, 18, "Mochila Promocional Nylon Ziper Preto 38cm Versatil 2 Placas", 117.50, None),
    (2, 19, "Mochila Pirulito Eventos Acoes Com 2 Placas Quadradas", 145.00, "BALCAO E BANDEJA"),
    (2, 20, "Mochila Pirulito Eventos Acoes Com 2 Placas Redondas", 145.00, "BALCAO E BANDEJA"),
    (2, 21, "Kit Com 4 Mochila Pirulito, Acoes Promocoes E Eventos", 714.92, None),
    (2, 22, "3 Mochilas Pirulito Sem Placas", 330.50, None),
    (2, 23, "Mochila Pirulito Eventos Acoes Com 2 Placas", 145.00, "BALCAO E BANDEJA"),
    (2, 24, "Mochila Escolar Juvenil Para Costas Pirulito Azul Estampada", 69.99, "DMW"),
    (2, 25, "Mochila Pirulito 2 Placas Divulgacao Movel Kit C/ 6 Pcs", 850.50, "CLAUDINHO DO SOM"),
    (2, 26, "Kit Com 10 Mochilas Pirulito Eventos Acoes Com 2 Placas", 1400.90, "BALCAO E BANDEJA"),
    (2, 27, "Mochila Pirulito 2 Placas Top, Acoes Promocoes E Eventos", 164.40, "AREAPROMOCIONAL"),
    (2, 28, "2 Mochilas Pirulito Sem Placas E Sem Haste", 199.17, "MOCHILA PIRULITO"),
    (2, 29, "2 Mochilas Pirulito + 2 Hastes E 4 Placas", 810.85, "AREAPROMOCIONAL"),
    (2, 30, "20 Mochilas Pirulito com Placas de 45cm e haste de 85cm", 2600.00, "MOCHILA PIRULITO"),
    (2, 31, "2 Mochila Pirulito Com 2 Placas Sem Impressao", 348.80, "AREAPROMOCIONAL"),
    (2, 32, "Kit Com 5 Mochilas Pirulito Com 2 Placas Lisas", 888.32, "AREAPROMOCIONAL"),
    (2, 33, "8 Mochilas Pirulito Com 2 Placas", 1034.40, "CLAUDINHO DO SOM"),
    (2, 34, "4 Mochila Pirulito Com 2 Placa Sem Impressao", 708.14, None),
    (2, 35, "Kit 4 Mochila Pirulito Com 2 Placas Quadradas 40x40cm", 720.69, "AREAPROMOCIONAL"),
    (2, 36, "10 Mochilas Pirulito Haste De 85cm", 1250.75, "MOCHILA PIRULITO"),
    (2, 37, "Mochila Pirulito Eventos Acoes Com 2 Placas Quadradas", 177.59, "AREAPROMOCIONAL"),
    (2, 38, "16 Mochilas Pirulito", 1990.00, "MOCHILA PIRULITO"),
    (2, 39, "10 Mochilas Pirulito Sem Placas", 1100.50, None),
    (2, 40, "Mochila Pirulito Com 1 Placa Quadrada 40cm Diametro", 176.93, "AREAPROMOCIONAL"),
    (2, 41, "2 Mochila Pirulito Com 2 Placas Sem Impressao", 357.60, None),
    (2, 42, "25 Mochilas Pirulito Sem Haste E Sem Placas", 2450.50, "MOCHILA PIRULITO"),
    (2, 43, "Kit Com 4 Mochila Pirulito Com 2 Placas Cada Mochilas Top", 624.33, "AREAPROMOCIONAL"),
    (2, 44, "Mochila Tipo Passeio Areapromocional Geometrica Ziper Propaganda", 810.33, "AREAPROMOCIONAL"),
    (2, 45, "Kit Com 4 Mochila Pirulito, Acoes Promocoes E Eventos", 708.14, None),
    (2, 46, "15 Mochilas Pirulito Sem Placas E Sem Haste", 1390.10, "MOCHILA PIRULITO"),
    (2, 47, "Mochila Pirulito Kit Com 10 Pcs", 1350.75, "CLAUDINHO DO SOM"),
    (2, 48, "6 Mochilas Pirulito Com 2 Placa Redonda 40cm Diametro", 1044.30, "MOCHILAS"),
    (2, 49, "Kit 10 Mochila Pirulito Com 2 Placas Cada Top Divulgacao", 1680.48, None),
    (2, 50, "10 Mochilas Pirulito Sem Placas E Sem Haste", 990.50, "MOCHILA PIRULITO"),
    (2, 51, "Mochila Pirulito 60cm Kit Com 6 Pcs", 1250.00, None),
    (2, 52, "20 Mochilas Pirulito Sem Placas", 2200.00, "MOCHILA PIRULITO"),
    (2, 53, "Kit Com 6 Mochila Pirulito 2 Placas Brancas Frete Gratis", 1080.03, "AREAPROMOCIONAL"),
    (2, 54, "Mochila Passeio Propaganda Personalizada Anunciar Liso Preto", 180.00, "PROPAGANDA PERSONALIZADA"),
    (2, 55, "Mochila Pirulito 38cm Kit Com 9 Pcs", 1125.50, "CLAUDINHO DO SOM"),
    (2, 56, "15 Mochilas Pirulito Com 2 Placas Cada", 1875.50, "MOCHILA PIRULITO"),
    (2, 57, "6 Mochilas Pirulito Com 2 Placa Redonda 40cm Diametro", 984.67, "AREAPROMOCIONAL"),
    (2, 58, "Kit Haste E Base Windflag 3,5m Semtecido", 215.88, None),
    (2, 59, "Mochila Pirulito, Mochila Evento Preto Liso", 90.00, None),
    (2, 60, "25 Mochilas Pirulito Sem Placas", 2750.50, None),

    # ===== PAGE 3 (60 products) =====
    (3, 1, "Mochila Pirulito Eventos Acoes Com 1 Placa Redonda", 135.00, "BALCAO E BANDEJA"),
    (3, 2, "Kit Com 4 Mochila Pirulito, Acoes Promocoes E Eventos", 714.92, None),
    (3, 3, "Mochila Pirulito Eventos 4 Unid Com 8 Placas", 550.58, "MOCHILA PIRULITO"),
    (3, 4, "Mochila Pirulito Propaganda Com 2 Placas Para Personalizar", 135.56, "CLAUDINHO DO SOM"),
    (3, 5, "Mochila Pirulito, Mochila Evento Preto Liso", 90.00, None),
    (3, 6, "25 Mochilas Pirulito Sem Placas", 2750.50, None),
    (3, 7, "6 Mochilas Pirulito Sem Placas", 549.09, None),
    (3, 8, "Mochila Areapromocional Pirulito Nylon Preto Alcas Reforcada", 2520.21, "AREAPROMOCIONAL"),
    (3, 9, "Mochila Pirulito Kit 10 Unidades, Mochila Propaganda", 899.90, "LUANA"),
    (3, 10, "Kit Mochila Roda Escolar Menina Miniee Poa Pirulito Rosa", 260.33, "PONTO VERDE"),
    (3, 11, "Mochila Pirulito Kit 5 Unidades | Sem Impressao", 860.00, None),
    (3, 12, "9 Mochilas Pirulito Propaganda Com 2 Placas Cada", 1125.50, "CLAUDINHO DO SOM"),
    (3, 13, "Mochila Pirulito Eventos Acoes Com 1 Placa", 135.00, "BALCAO E BANDEJA"),
    (3, 14, "Mochila Pirulito Com 2 Placas Sem Impressao Cor Preto", 164.40, "PROPAGANDA PERSONALIZADA"),
    (3, 15, "Mochila Pirulito - Preto Liso (kit Com 05 Unidades) Caixa", 670.80, None),
    (3, 16, "Mochila Pirulito 2 Placas Brancas Frete Gratis E 12x S/juros", 174.62, None),
    (3, 17, "Kit Com 8 Mochilas Pirulito Com 2 Placas Lisas", 1416.33, "AREAPROMOCIONAL"),
    (3, 18, "Kit Com 10 Mochilas Pirulito Eventos Acoes Com 2 Placas", 1400.90, "BALCAO E BANDEJA"),
    (3, 19, "Mochila Pirulito Kit 2 Unidades | Sem Impressao", 359.90, None),
    (3, 20, "Kit Com 10 Mochilas Pirulito Com 2 Placas Lisas", 1680.72, None),
    (3, 21, "Mochila Pirulito Kit 4 Unidades | Sem Impressao", 719.80, None),
    (3, 22, "Mochila Dermiwil Container Escolar Feminina", 111.99, "DERMIWIL"),
    (3, 23, "Mochila Pirulito - Kit 10 Unidades Sem Impressao", 1690.00, None),
    (3, 24, "Mochila Led Impermeavel 30l Personalizavel Com App Rgb", 899.90, "VIRTUAFX"),
    (3, 25, "Mochila Pirulito 2 Placas Divulgacao Movel Kit C/ 6 Pcs", 850.50, "CLAUDINHO DO SOM"),
    (3, 26, "Kit Com 10 Mochilas Pirulito Eventos Acoes Com 2 Placas", 1400.90, "BALCAO E BANDEJA"),
    (3, 27, "Mochila Pirulito 2 Placas Top, Acoes Promocoes E Eventos", 164.40, "AREAPROMOCIONAL"),
    (3, 28, "2 Mochilas Pirulito Sem Placas E Sem Haste", 199.17, "MOCHILA PIRULITO"),
    (3, 29, "Kit Com 5 Mochilas Pirulito Eventos Acoes Com 2 Placas", 700.69, "BALCAO E BANDEJA"),
    (3, 30, "Kit 5 Mochilas Pirulito Eventos Acoes Com 2 Placas Quadradas", 700.69, "BALCAO E BANDEJA"),
    (3, 31, "Kit 10 Mochila Pirulito Eventos Acoes Com 1 Placa Quadrada", 1300.20, "BALCAO E BANDEJA"),
    (3, 32, "Mochila Preta Areapromocional Geometrica Ziper Propaganda", 2280.50, "AREAPROMOCIONAL"),
    (3, 33, "Kit 10 Mochila Pirulito Eventos Acoes Com 2 Placas Quadradas", 1400.90, "BALCAO E BANDEJA"),
    (3, 34, "Kit 5 Mochilas Pirulito Eventos Acoes Com 1 Placa Redonda", 650.86, "BALCAO E BANDEJA"),
    (3, 35, "Kit 5 Mochilas Pirulito Eventos Acoes Com 1 Placa Quadrada", 650.86, "BALCAO E BANDEJA"),
    (3, 36, "Kit Com 5 Mochilas Pirulito Eventos Acoes Com 1 Placa Preto", 650.86, "BALCAO E BANDEJA"),
    (3, 37, "Kit 5 Mochilas Pirulito Eventos Acoes Com 2 Placas Redondas", 700.69, "BALCAO E BANDEJA"),
    (3, 38, "Kit 15 Mochila Pirulito Eventos Acoes Com 2 Placas Quadradas", 2100.84, "BALCAO E BANDEJA"),
    (3, 39, "Mochila Pirulito Com 1 Placa Com Sua Impressao", 234.12, "AREAPROMOCIONAL"),
    (3, 40, "Kit 20 Mochila Pirulito Eventos Acoes Com 1 Placa Quadrada", 2600.90, "BALCAO E BANDEJA"),
    (3, 41, "Kit 20 Mochila Pirulito Eventos Acoes Com 2 Placas Quadradas", 2800.13, "BALCAO E BANDEJA"),
    (3, 42, "Kit 15 Mochilas Pirulito Eventos Acoes Com 1 Placa Redonda", 1950.43, "BALCAO E BANDEJA"),
    (3, 43, "Kit 10 Mochilas Pirulito Eventos Acoes Com 1 Placa Redonda", 1300.20, "BALCAO E BANDEJA"),
    (3, 44, "Mochila Infantil Elegancia De Pirulito E Unicornio", 65.99, "FAVEL"),
    (3, 45, "Kit 15 Mochila Pirulito Eventos Acoes Com 1 Placa Quadrada", 1950.43, "BALCAO E BANDEJA"),
    (3, 46, "Kit Com 10 Mochilas Pirulito Eventos Acoes Com 1 Placa", 1300.20, "BALCAO E BANDEJA"),
    (3, 47, "Kit 15 Mochilas Pirulito Eventos Acoes Com 2 Placas Redondas", 2100.84, "BALCAO E BANDEJA"),
    (3, 48, "Kit 10 Mochilas Pirulito Eventos Acoes Com 2 Placas Redondas", 1400.90, "BALCAO E BANDEJA"),
    (3, 49, "Kit Com 15 Mochilas Pirulito Eventos Acoes Com 2 Placas", 2100.84, "BALCAO E BANDEJA"),
    (3, 50, "Kit Com 20 Mochilas Pirulito Eventos Acoes Com 1 Placa", 2600.90, "BALCAO E BANDEJA"),
    (3, 51, "Kit Com 15 Mochilas Pirulito Eventos Acoes Com 1 Placa", 1950.43, "BALCAO E BANDEJA"),
    (3, 52, "Kit 20 Mochilas Pirulito Eventos Acoes Com 1 Placa Redonda", 2600.90, "BALCAO E BANDEJA"),
    (3, 53, "Mochila Pirulito Iluminada Para Personalizar Usb Power Bank", 477.60, None),
    (3, 54, "Mochila Pirulito Iluminada Usb Power Bank Led", 468.25, None),
    (3, 55, "Mochila Pirulito Eventos Acoes Com 2 Placas", 199.00, None),
    (3, 56, "Mochila Elegante De Pirulito Fluorescente", 64.64, None),
    (3, 57, "Kit 20 Mochilas Pirulito Eventos Acoes Com 2 Placas Redondas", 2800.13, "BALCAO E BANDEJA"),
    (3, 58, "Kit Com 20 Mochilas Pirulito Eventos Acoes Com 2 Placas", 2800.13, "BALCAO E BANDEJA"),
    (3, 59, "Personagem De Anime Com Mochila Apontando Pirulito", 40.48, None),
    (3, 60, "5 Mochila Pirulito Iluminada 30 Com Power Bank", 2280.31, None),

    # ===== PAGE 4 (60 products) =====
    (4, 1, "Kit Com 4 Mochila Pirulito, Acoes Promocoes E Eventos", 714.92, None),
    (4, 2, "Mochila Pirulito Eventos 4 Unid Com 8 Placas", 550.58, "MOCHILA PIRULITO"),
    (4, 3, "Mochila Pirulito Eventos Acoes Com 1 Placa", 135.00, "BALCAO E BANDEJA"),
    (4, 4, "Mochila Pirulito - Preto Liso (kit Com 05 Unidades) Caixa", 670.80, None),
    (4, 5, "5 Mochila Pirulito Iluminada 30 Com Power Bank", 2280.31, None),
    (4, 6, "Mochila Feminina Casual Escolar Viagem Pirulito", 236.81, None),
    (4, 7, "Minion Em Roupa Dos Anos 70 Com Mochila Pirulito", 118.77, None),
    (4, 8, "Mochila Pirulito Rosa Mochila Leve Com Ajuste", 116.58, None),
    (4, 9, "Mochila Feminina Casual Escolar Viagem Pirulito", 168.77, None),
    (4, 10, "Mochila Feminina Casual Escolar Viagem Pirulito", 165.74, None),
    (4, 11, "Mochila Feminina Casual Escolar Viagem Pirulito", 168.72, None),
    (4, 12, "Mochila Feminina Casual Escolar Viagem Pirulito", 165.74, None),
    (4, 13, "Mochila Pirulito 2 Placas Divulgacao Movel Kit C/ 6 Pcs", 850.50, "CLAUDINHO DO SOM"),
    (4, 14, "Kit Com 10 Mochilas Pirulito Eventos Acoes Com 2 Placas", 1400.90, "BALCAO E BANDEJA"),
    (4, 15, "2 Mochilas Pirulito Sem Placas E Sem Haste", 199.17, "MOCHILA PIRULITO"),
    (4, 16, "Mochila Pirulito Eventos Acoes Com 1 Placa Quadrada", 135.00, "BALCAO E BANDEJA"),
    (4, 17, "Mochila Pirulito Com 2 Placas Sem Impressao", 174.68, "AREAPROMOCIONAL"),
    (4, 18, "Mochila Feminina Casual Escolar Viagem Pirulito", 216.47, None),
    (4, 19, "Mochila Para Meninas, Viagem Casual, Pirulito, Bolsa Escolar", 180.91, None),
    (4, 20, "Mochila Feminina Casual Escolar Viagem Pirulito", 206.17, None),
    (4, 21, "Mochila Feminina Casual Escolar Viagem Pirulito", 218.30, None),
    (4, 22, "Mochila Feminina Casual Escolar Viagem Pirulito", 214.59, None),
    (4, 23, "Mochila Feminina Casual De Viagem Pirulito Bolsa Escolar", 154.34, None),
    (4, 24, "Mochila Feminina Casual De Viagem Pirulito Bolsa Escolar", 152.40, None),
    (4, 25, "Mochila Pirulito Propaganda Com 2 Placas 38cm Cor Preto", 134.90, None),
    (4, 26, "Mochila Pirulito Eventos Acoes Com 2 Placas Quadradas", 145.00, "BALCAO E BANDEJA"),
    (4, 27, "2 Mochilas Pirulito + 2 Hastes E 4 Placas", 810.85, "AREAPROMOCIONAL"),
    (4, 28, "6 Mochilas Pirulito Com 2 Placa Redonda 40cm Diametro", 1044.30, "MOCHILAS"),
    (4, 29, "Mochila Para Meninas, Viagem Casual, Pirulito, Bolsa Escolar", 165.95, None),
    (4, 30, "Mochila Feminina Casual De Viagem Pirulito Bolsa Escolar", 154.34, None),
    (4, 31, "Mochila Feminina Casual De Viagem Pirulito Bolsa Escolar", 206.17, None),
    (4, 32, "Mochila Feminina Casual De Viagem Pirulito Bolsa Escolar", 155.64, None),
    (4, 33, "Mochila Feminina Casual De Viagem Pirulito Bolsa Escolar", 154.39, None),
    (4, 34, "3 Mochilas Pirulito Com Placas Personalizadas", 550.00, None),
    (4, 35, "Mochila Para Meninas, Viagem Casual, Pirulito, Bolsa Escolar", 165.95, None),
    (4, 36, "Mochila Para Meninas, Viagem Casual, Pirulito, Bolsa Escolar", 180.91, None),
    (4, 37, "Mochila Escolar Com Pirulito De Coracao De Hatsune Miku", 148.17, None),
    (4, 38, "Mochila Pirulito Eventos Acoes Com 2 Placas Personalizadas", 312.40, "AREAPROMOCIONAL"),
    (4, 39, "2 Mochilas Pirulito Com Placas Personalizadas", 419.38, None),
    (4, 40, "Kit 2 Mochila Pirulito 2 Placas Personalizadas Sua Impressao", 520.80, None),
    (4, 41, "Kit Com 20 Unidades Mochilas Pirulito Mochila Placa Redonda", 3000.45, "MOCHILA PIRULITO"),
    (4, 42, "8 Mochilas Pirulito Personalizadas Frente E Verso", 1550.00, "MOCHILA PIRULITO"),
    (4, 43, "5 Mochilas Pirulito Com Placas Personalizadas", 875.50, None),
    (4, 44, "10 Mochilas Pirulito Placas Personalizadas Frente E Verso", 1990.00, "MOCHILA PIRULITO"),
    (4, 45, "8 Mochilas Pirulito Personalizadas Frente E Verso", 1408.80, "MOCHILA PIRULITO"),
    (4, 46, "Mochila Pirulito Com 2 Placas Com Sua Impressao", 261.60, None),
    (4, 47, "7 Mochilas Pirulito Personalizadas Frente E Verso", 1393.30, "MOCHILA PIRULITO"),
    (4, 48, "6 Mochilas Pirulito Personalizadas Frente Verso", 1260.00, "MOCHILA PIRULITO"),
    (4, 49, "20 Mochilas Pirulito Personalizadas Frente E Verso", 3500.00, "MOCHILA PIRULITO"),
    (4, 50, "Kit 1 Mochilas Pirulito Com 2 Placas Ja Com Personalizacao", 261.60, "AREAPROMOCIONAL"),
    (4, 51, "1 Mochila Pirulito 2 Placas Personalizadas Sua Impressao", 216.20, "BALCAO E BANDEJA"),
    (4, 52, "16 Mochilas Pirulito Personalizadas", 2977.75, "MOCHILA PIRULITO"),
    (4, 53, "Mochila Pirulito Eventos Acoes Com 2 Placas Quadradas", 167.99, "AREAPROMOCIONAL"),
    (4, 54, "5 Mochilas Pirulito 2 Placas Com Sua Impressao Frete Gratis", 1140.76, "AREAPROMOCIONAL"),
    (4, 55, "Kit 10 Mochilas Pirulito Com 2 Placas Com Sua Impressao", 2280.31, "AREAPROMOCIONAL"),
    (4, 56, "Mochila Escolar Com Pirulito Cinnamoroll E Faixa Rosa Cereja", 71.49, "GENERAL"),
    (4, 57, "Mochilas Pirulito Divulgacao Personalizada Com Sua Marca", 139.90, "MIDIAS"),
    (4, 58, "Mochilas Divulgacao Pirulito Sem Personalizar", 78.80, "GRP"),
    (4, 59, "Mochilas Divulgacao Pirulito Sem Personalizar", 78.90, "MIDIAS"),
    (4, 60, "Mochilas Divulgacao Pirulito Sem Personalizar Preto", 78.90, "MIDIAS"),

    # ===== PAGE 5 (20 products) =====
    (5, 1, "Kit Com 4 Mochila Pirulito, Acoes Promocoes E Eventos", 714.92, None),
    (5, 2, "Kit Com 10 Mochilas Pirulito Eventos Acoes Com 2 Placas", 1400.90, "BALCAO E BANDEJA"),
    (5, 3, "2 Mochilas Pirulito Sem Placas E Sem Haste", 199.17, "MOCHILA PIRULITO"),
    (5, 4, "Mochila Pirulito Eventos Acoes Com 2 Placas Quadradas", 145.00, "BALCAO E BANDEJA"),
    (5, 5, "Mochilas Divulgacao Pirulito Sem Personalizar", 78.90, "MIDIAS"),
    (5, 6, "Mochilas Divulgacao Pirulito Sem Personalizar Preto", 78.90, "MIDIAS"),
    (5, 7, "Ki 20 Mochilas Pirulito Sem Personalizar Duas Placas", 1578.80, "MIDIAS"),
    (5, 8, "Mochilas Pirulito Divulgacao Personalizada Com Sua Marca", 139.90, "MIDIAS"),
    (5, 9, "Mochilas Pirulito Personalizada Com Sua Marca Preto", 150.00, "MIDIAS"),
    (5, 10, "2x Mochilas Divulgacao Pirulito Personalizada", 278.90, "GRP"),
    (5, 11, "Mochila Banner Pirolito Com Placa E Haste De Aluminio", 159.99, None),
    (5, 12, "Kit 4 Mochilas Pirulito Sem Personalizar Duas Placas", 313.90, "MIDIAS"),
    (5, 13, "Mochilas Pirulito Divulgacao Personalizada Com Sua Marca", 135.90, "MIDIAS"),
    (5, 14, "Mochila Pirulito Com Placas Frente E Verso Personalizada Df", 139.90, "MIDIAS INTELIGENTES"),
    (5, 15, "Kit 2 Mochilas Pirulito Divulgacao Personalizada Sua Marca", 269.90, "MIDIAS"),
    (5, 16, "15x Mochilas Pirulito Personalizada Com Sua Marca Preto", 1850.75, "MIDIAS"),
    (5, 17, "2 Mochilas Pirulito + 2 Hastes E 4 Placas", 810.85, "AREAPROMOCIONAL"),
    (5, 18, "6 Mochilas Pirulito Com 2 Placa Redonda 40cm Diametro", 1044.30, "MOCHILAS"),
    (5, 19, "4 Mochila Pirulito Com 1 Placa Sem Impressao", 648.28, None),
    (5, 20, "Mochila Promocional Nylon Ziper Preto 38cm Versatil 2 Placas", 117.50, None),
]


# ---------------------------------------------------------------------------
# 2. CLASSIFICATION HELPERS
# ---------------------------------------------------------------------------

# Non-relevant product patterns (NOT promotional mochila pirulito)
NON_RELEVANT_PATTERNS = [
    r"(?i)mochila\s+escolar\s+com\s+pirulito\s+de\s+cora",        # Hatsune Miku
    r"(?i)mochila\s+escolar\s+juvenil.*pirulito\s+azul",           # DMW school backpack
    r"(?i)mochila\s+dermiwil\s+container\s+escolar",               # Dermiwil school
    r"(?i)mochila\s+infantil\s+elegancia\s+de\s+pirulito",         # Kids unicorn
    r"(?i)mochila\s+elegante\s+de\s+pirulito\s+fluorescente",      # Fashion
    r"(?i)personagem\s+de\s+anime\s+com\s+mochila",                # Anime figurine
    r"(?i)mochila\s+feminina\s+casual.*pirulito",                   # Women's casual
    r"(?i)mochila\s+para\s+meninas.*pirulito.*bolsa\s+escolar",    # Girls school
    r"(?i)kit\s+mochila\s+roda\s+escolar\s+menina",               # Girls wheeled
    r"(?i)mochila\s+led\s+impermeavel.*personalizavel",            # LED backpack (not pirulito promo)
    r"(?i)minion\s+em\s+roupa.*mochila\s+pirulito",               # Minion figurine
    r"(?i)mochila\s+pirulito\s+rosa\s+mochila\s+leve",            # Pink casual
    r"(?i)kit\s+haste\s+e\s+base\s+windflag",                     # Windflag (not mochila)
    r"(?i)mochila\s+escolar\s+com\s+pirulito\s+cinnamoroll",      # Cinnamoroll school
    r"(?i)mochila\s+tipo\s+passeio\s+areapromocional\s+geometrica",# Passeio style (not pirulito)
    r"(?i)mochila\s+preta\s+areapromocional\s+geometrica",        # Passeio style
    r"(?i)mochila\s+passeio\s+propaganda\s+personalizada\s+anunciar", # Passeio style
]

# Accessory-only patterns (hastes/placas without mochila)
ACCESSORY_PATTERNS = [
    r"(?i)^\d*\s*hastes?\s+e\s+\d+\s+placas?\s+para\s+mochila",  # "1 Hastes E 2 Placas Para Mochila Pirulito Sem Mochila!!"
]


def is_non_relevant(title):
    """Check if a product is NOT a promotional mochila pirulito."""
    for pat in NON_RELEVANT_PATTERNS:
        if re.search(pat, title):
            return True
    return False


def is_accessory_only(title):
    """Check if a listing is accessories only (no backpack)."""
    for pat in ACCESSORY_PATTERNS:
        if re.search(pat, title):
            return True
    return False


def extract_quantity(title):
    """
    Extract the quantity of mochilas from the title.
    Returns (quantity, is_kit).
    """
    title_lower = title.lower()

    # Pattern: "Kit Com X Mochila(s)" or "Kit X Mochila(s)"
    m = re.search(r"(?i)ki(?:t)?\s+(?:com\s+)?(\d+)\s+(?:un(?:idades?)?|mochilas?|mochila)", title)
    if m:
        return int(m.group(1)), True

    # Pattern: "X Mochilas Pirulito" or "X Mochila Pirulito" at start
    m = re.search(r"(?i)^(\d+)x?\s+mochilas?\s+pirulito", title)
    if m:
        return int(m.group(1)), True

    # Pattern: "(kit Com XX Unidades)"
    m = re.search(r"(?i)\(kit\s+com\s+(\d+)\s+unidades?\)", title)
    if m:
        return int(m.group(1)), True

    # Pattern: "kit Com X Pecas" or "kit C/ X Pcs"
    m = re.search(r"(?i)kit\s+(?:com\s+|c/\s*)(\d+)\s+(?:pecas?|pcs|p[eç]as?)", title)
    if m:
        return int(m.group(1)), True

    # Pattern: "X Unid Com Y Placas" (e.g. "4 Unid Com 8 Placas")
    m = re.search(r"(?i)(\d+)\s+unid(?:ades?)?\s+com", title)
    if m:
        return int(m.group(1)), True

    # Pattern: "Propaganda 2 Pecas"
    m = re.search(r"(?i)propaganda\s+(\d+)\s+pecas?", title)
    if m:
        return int(m.group(1)), True

    # Pattern: "Kit X Mochilas" (without "pirulito" after)
    m = re.search(r"(?i)ki(?:t)?\s+(?:com\s+)?(\d+)\s+mochilas?", title)
    if m:
        return int(m.group(1)), True

    # Pattern: "X Mochilas Pirulito" anywhere (not just start)
    m = re.search(r"(?i)(\d+)\s+mochilas?\s+pirulito", title)
    if m:
        return int(m.group(1)), True

    # Pattern: "Divulgacao Movel Kit C/ X Pcs"
    m = re.search(r"(?i)kit\s+c/\s*(\d+)\s+pcs", title)
    if m:
        return int(m.group(1)), True

    # Pattern: "03 Un Mochila"
    m = re.search(r"(?i)^(\d+)\s+un\s+mochila", title)
    if m:
        return int(m.group(1)), True

    # Pattern: "Xx Mochilas Divulgacao"
    m = re.search(r"(?i)^(\d+)x?\s+mochilas?\s+(?:divulgacao|propaganda)", title)
    if m:
        return int(m.group(1)), True

    # Pattern: "Kit 1 Mochilas" (explicit 1)
    m = re.search(r"(?i)ki(?:t)?\s+1\s+mochilas?", title)
    if m:
        return 1, False

    # Pattern: "Mochila Pirulito Kit X Unidades"
    m = re.search(r"(?i)kit\s+(\d+)\s+unidades?", title)
    if m:
        return int(m.group(1)), True

    # Pattern: "5 Mochila Pirulito Iluminada"
    m = re.search(r"(?i)^(\d+)\s+mochila\s+pirulito", title)
    if m:
        qty = int(m.group(1))
        if qty > 1:
            return qty, True
        return 1, False

    return 1, False


def normalize_seller(seller_raw):
    """Normalize seller name, merging aliases."""
    if seller_raw is None:
        return "NAO IDENTIFICADO"
    s = seller_raw.strip().upper()
    # Merge aliases
    if s in ("AREAPROMOCIONAL POR DOUTO", "AREAPROMOCIONAL POR DOUTOR BEER"):
        return "AREAPROMOCIONAL"
    if s == "DOUTOR BEER":
        return "DOUTOR BEER"
    if s == "MIDIAS INTELIGENTES":
        return "MIDIAS INTELIGENTES"  # keep separate from MIDIAS
    return s


def categorize_quantity(qty):
    """Categorize by kit size."""
    if qty == 1:
        return "Unidade"
    elif qty <= 5:
        return "Kit 2-5"
    elif qty <= 10:
        return "Kit 6-10"
    else:
        return "Kit 10+"


def is_personalized(title):
    """Check if the product includes personalization/printing."""
    patterns = [
        r"(?i)personalizada",
        r"(?i)personalizado",
        r"(?i)personalizadas",
        r"(?i)personaliz[aá]",
        r"(?i)com\s+sua\s+impress[aã]o",
        r"(?i)com\s+sua\s+marca",
        r"(?i)j[aá]\s+com\s+personaliza",
    ]
    for p in patterns:
        if re.search(p, title):
            return True
    return False


def classify_product(title):
    """
    Classifica o produto em varias dimensoes baseado no titulo.
    Retorna dict com: tipo_produto, qtd_placas, formato_placa, tamanho, inclui_haste
    """
    t = title.lower()

    # --- Tipo de produto ---
    if re.search(r"iluminada|led|power\s*bank", t):
        tipo = "Iluminada/LED"
    elif re.search(r"caixa\s+m[oó]vel", t):
        tipo = "Caixa Movel"
    elif re.search(r"sem\s+placa.*sem\s+haste|sem\s+haste.*sem\s+placa|s[oó]\s+a?\s*mochila", t):
        tipo = "So Mochila (sem placa/haste)"
    elif re.search(r"sem\s+placa", t):
        tipo = "Sem Placa"
    elif re.search(r"sem\s+personalizar|sem\s+impress", t):
        tipo = "Lisa (sem impressao)"
    elif re.search(r"propaganda|divulga[cç][aã]o|publicidade|eventos|a[cç][oõ]es|promo[cç]", t):
        tipo = "Propaganda/Eventos"
    else:
        tipo = "Padrao"

    # --- Quantidade de placas ---
    m_placas = re.search(r"(\d+)\s*placas?", t)
    if m_placas:
        qtd_placas = int(m_placas.group(1))
    elif re.search(r"sem\s+placa", t):
        qtd_placas = 0
    else:
        qtd_placas = None  # nao especificado

    # --- Formato da placa ---
    if re.search(r"redonda", t):
        formato = "Redonda"
    elif re.search(r"quadrada|40x40|40cm", t):
        formato = "Quadrada"
    else:
        formato = None  # nao especificado

    # --- Tamanho ---
    m_tam = re.search(r"(\d{2,3})\s*cm", t)
    tamanho = f"{m_tam.group(1)}cm" if m_tam else None

    # --- Inclui haste ---
    if re.search(r"sem\s+haste", t):
        inclui_haste = "Nao"
    elif re.search(r"haste|com\s+haste", t):
        inclui_haste = "Sim"
    else:
        inclui_haste = None  # nao especificado

    # --- Material/diferencial ---
    diferenciais = []
    if re.search(r"duratran", t):
        diferenciais.append("Duratran")
    if re.search(r"imperme[aá]vel", t):
        diferenciais.append("Impermeavel")
    if re.search(r"nylon", t):
        diferenciais.append("Nylon")
    if re.search(r"alum[ií]nio", t):
        diferenciais.append("Haste Aluminio")
    if re.search(r"bolso\s+lateral", t):
        diferenciais.append("Bolso Lateral")
    if re.search(r"z[ií]per", t):
        diferenciais.append("Ziper")

    return {
        "tipo_produto": tipo,
        "qtd_placas": qtd_placas,
        "formato_placa": formato,
        "tamanho": tamanho,
        "inclui_haste": inclui_haste,
        "diferenciais": ", ".join(diferenciais) if diferenciais else None,
    }


# ---------------------------------------------------------------------------
# 3. DEDUPLICATION
# ---------------------------------------------------------------------------

def deduplicate(raw_data):
    """
    Remove duplicate listings across pages.
    A duplicate is defined as same title + same price (+ same seller if identified).
    We keep the first occurrence (lowest page number).
    """
    seen = set()
    unique = []
    for page, idx, title, price, seller in raw_data:
        # Normalize title for comparison
        title_norm = re.sub(r'\s+', ' ', title.strip().lower())
        key = (title_norm, price, normalize_seller(seller))
        if key not in seen:
            seen.add(key)
            unique.append((page, idx, title, price, seller))
    return unique


# ---------------------------------------------------------------------------
# 4. MAIN ANALYSIS
# ---------------------------------------------------------------------------

def run_analysis():
    print("=" * 80)
    print("  ANALISE DE CONCORRENTES - MOCHILA PIRULITO (MERCADO LIVRE)")
    print("  Dados: 5 paginas de busca, coletados em 02/03/2026")
    print("=" * 80)

    total_raw = len(RAW_DATA)
    print(f"\nTotal de registros brutos (5 paginas): {total_raw}")

    # --- Step 1: Deduplicate ---
    unique_data = deduplicate(RAW_DATA)
    n_dupes = total_raw - len(unique_data)
    print(f"Duplicatas removidas: {n_dupes}")
    print(f"Registros unicos: {len(unique_data)}")

    # --- Step 2: Classify ---
    products = []
    non_relevant_list = []
    accessory_list = []

    for page, idx, title, price, seller_raw in unique_data:
        seller = normalize_seller(seller_raw)

        if is_non_relevant(title):
            non_relevant_list.append({
                "pagina": page,
                "titulo": title,
                "preco_total": price,
                "vendedor": seller,
                "motivo": "Nao e mochila pirulito promocional",
            })
            continue

        if is_accessory_only(title):
            accessory_list.append({
                "pagina": page,
                "titulo": title,
                "preco_total": price,
                "vendedor": seller,
                "motivo": "Acessorio (haste/placa) sem mochila",
            })
            continue

        qty, is_kit = extract_quantity(title)
        unit_price = round(price / qty, 2) if qty > 0 else price
        category = categorize_quantity(qty)
        personalized = is_personalized(title)
        classif = classify_product(title)

        products.append({
            "pagina_orig": page,
            "titulo": title,
            "preco_total": price,
            "quantidade": qty,
            "preco_unitario": unit_price,
            "vendedor": seller,
            "categoria_kit": category,
            "personalizada": personalized,
            "tipo_produto": classif["tipo_produto"],
            "qtd_placas": classif["qtd_placas"],
            "formato_placa": classif["formato_placa"],
            "tamanho": classif["tamanho"],
            "inclui_haste": classif["inclui_haste"],
            "diferenciais": classif["diferenciais"],
        })

    print(f"\n--- CLASSIFICACAO ---")
    print(f"Produtos RELEVANTES (mochila pirulito promocional): {len(products)}")
    print(f"Produtos NAO RELEVANTES (escolar/infantil/figurinha): {len(non_relevant_list)}")
    print(f"Acessorios (haste/placa apenas): {len(accessory_list)}")

    df = pd.DataFrame(products)
    df_nonrel = pd.DataFrame(non_relevant_list)
    df_access = pd.DataFrame(accessory_list)

    # --- Step 3: Analysis ---

    # 3a. Price distribution (unit prices of relevant products)
    print(f"\n{'=' * 80}")
    print("  DISTRIBUICAO DE PRECOS UNITARIOS (produtos relevantes)")
    print(f"{'=' * 80}")

    # Separate personalized vs non-personalized
    df_plain = df[~df["personalizada"]].copy()
    df_pers = df[df["personalizada"]].copy()

    # Filter out illuminated/LED products for clean stats
    is_illum_all = df["titulo"].str.contains(r"(?i)iluminada|led|power\s*bank", regex=True)
    df_standard = df[~is_illum_all].copy()
    df_plain_std = df_plain[~df_plain["titulo"].str.contains(r"(?i)iluminada|led|power\s*bank", regex=True)].copy()
    # Also exclude extreme outliers (unit > R$500)
    df_plain_clean = df_plain_std[df_plain_std["preco_unitario"] <= 500].copy()

    print(f"\n  SEM personalizacao - LIMPO ({len(df_plain_clean)} anuncios, sem iluminadas/outliers):")
    if len(df_plain_clean) > 0:
        stats_clean = df_plain_clean["preco_unitario"].describe()
        print(f"    Minimo:  R$ {stats_clean['min']:.2f}")
        print(f"    Maximo:  R$ {stats_clean['max']:.2f}")
        print(f"    Media:   R$ {stats_clean['mean']:.2f}")
        print(f"    Mediana: R$ {stats_clean['50%']:.2f}")
        print(f"    Desvio:  R$ {stats_clean['std']:.2f}")

    print(f"\n  SEM personalizacao - TODOS ({len(df_plain)} anuncios, inclui iluminadas):")
    if len(df_plain) > 0:
        stats_plain = df_plain["preco_unitario"].describe()
        print(f"    Minimo:  R$ {stats_plain['min']:.2f}")
        print(f"    Maximo:  R$ {stats_plain['max']:.2f}")
        print(f"    Media:   R$ {stats_plain['mean']:.2f}")
        print(f"    Mediana: R$ {stats_plain['50%']:.2f}")
        print(f"    Desvio:  R$ {stats_plain['std']:.2f}")

    print(f"\n  COM personalizacao ({len(df_pers)} anuncios):")
    if len(df_pers) > 0:
        stats_pers = df_pers["preco_unitario"].describe()
        print(f"    Minimo:  R$ {stats_pers['min']:.2f}")
        print(f"    Maximo:  R$ {stats_pers['max']:.2f}")
        print(f"    Media:   R$ {stats_pers['mean']:.2f}")
        print(f"    Mediana: R$ {stats_pers['50%']:.2f}")
        print(f"    Desvio:  R$ {stats_pers['std']:.2f}")

    print(f"\n  TODOS ({len(df)} anuncios):")
    stats_all = df["preco_unitario"].describe()
    print(f"    Minimo:  R$ {stats_all['min']:.2f}")
    print(f"    Maximo:  R$ {stats_all['max']:.2f}")
    print(f"    Media:   R$ {stats_all['mean']:.2f}")
    print(f"    Mediana: R$ {stats_all['50%']:.2f}")
    print(f"    Desvio:  R$ {stats_all['std']:.2f}")

    # Price ranges
    bins = [0, 80, 100, 120, 140, 160, 180, 200, 250, 500, float("inf")]
    labels = [
        "Ate R$80", "R$80-100", "R$100-120", "R$120-140",
        "R$140-160", "R$160-180", "R$180-200", "R$200-250",
        "R$250-500", "R$500+"
    ]
    df["faixa_preco_unit"] = pd.cut(df["preco_unitario"], bins=bins, labels=labels, right=False)
    price_dist = df["faixa_preco_unit"].value_counts().sort_index()
    print(f"\n  Distribuicao por faixa de preco unitario:")
    for faixa, count in price_dist.items():
        bar = "#" * count
        print(f"    {faixa:<15} {count:>3} {bar}")

    # 3b. Categories by kit size
    print(f"\n{'=' * 80}")
    print("  CATEGORIAS POR TAMANHO DE KIT")
    print(f"{'=' * 80}")
    cat_summary = df.groupby("categoria_kit").agg(
        qtd_anuncios=("titulo", "count"),
        preco_unit_min=("preco_unitario", "min"),
        preco_unit_max=("preco_unitario", "max"),
        preco_unit_medio=("preco_unitario", "mean"),
        preco_unit_mediana=("preco_unitario", "median"),
    ).reindex(["Unidade", "Kit 2-5", "Kit 6-10", "Kit 10+"])
    cat_summary["preco_unit_medio"] = cat_summary["preco_unit_medio"].round(2)
    cat_summary["preco_unit_mediana"] = cat_summary["preco_unit_mediana"].round(2)

    for cat_name, row in cat_summary.iterrows():
        print(f"\n  {cat_name}:")
        print(f"    Anuncios:        {int(row['qtd_anuncios'])}")
        print(f"    Preco unit min:  R$ {row['preco_unit_min']:.2f}")
        print(f"    Preco unit max:  R$ {row['preco_unit_max']:.2f}")
        print(f"    Preco unit medio:R$ {row['preco_unit_medio']:.2f}")
        print(f"    Preco unit med.: R$ {row['preco_unit_mediana']:.2f}")

    # 3c. Sellers analysis
    print(f"\n{'=' * 80}")
    print("  VENDEDORES - RANKING POR NUMERO DE ANUNCIOS")
    print(f"{'=' * 80}")

    seller_stats = df.groupby("vendedor").agg(
        qtd_anuncios=("titulo", "count"),
        preco_unit_min=("preco_unitario", "min"),
        preco_unit_max=("preco_unitario", "max"),
        preco_unit_medio=("preco_unitario", "mean"),
        preco_unit_mediana=("preco_unitario", "median"),
        preco_total_min=("preco_total", "min"),
        preco_total_max=("preco_total", "max"),
    ).sort_values("qtd_anuncios", ascending=False)
    seller_stats["preco_unit_medio"] = seller_stats["preco_unit_medio"].round(2)
    seller_stats["preco_unit_mediana"] = seller_stats["preco_unit_mediana"].round(2)

    for rank, (seller, row) in enumerate(seller_stats.iterrows(), 1):
        print(f"\n  {rank}. {seller}")
        print(f"     Anuncios: {int(row['qtd_anuncios'])}")
        print(f"     Preco unitario: R$ {row['preco_unit_min']:.2f} ~ R$ {row['preco_unit_max']:.2f} "
              f"(media R$ {row['preco_unit_medio']:.2f}, mediana R$ {row['preco_unit_mediana']:.2f})")
        print(f"     Preco total anuncio: R$ {row['preco_total_min']:.2f} ~ R$ {row['preco_total_max']:.2f}")

    # 3d. Top sellers by unit price (only identified sellers, excluding "NAO IDENTIFICADO")
    print(f"\n{'=' * 80}")
    print("  PRECO UNITARIO MEDIO POR VENDEDOR IDENTIFICADO (sem personalizacao)")
    print(f"{'=' * 80}")

    df_identified_plain = df_plain[df_plain["vendedor"] != "NAO IDENTIFICADO"]
    if len(df_identified_plain) > 0:
        seller_unit = df_identified_plain.groupby("vendedor").agg(
            qtd_anuncios=("titulo", "count"),
            preco_unit_medio=("preco_unitario", "mean"),
            preco_unit_mediana=("preco_unitario", "median"),
            preco_unit_min=("preco_unitario", "min"),
            preco_unit_max=("preco_unitario", "max"),
        ).sort_values("preco_unit_medio")
        seller_unit["preco_unit_medio"] = seller_unit["preco_unit_medio"].round(2)
        seller_unit["preco_unit_mediana"] = seller_unit["preco_unit_mediana"].round(2)

        for seller, row in seller_unit.iterrows():
            print(f"  {seller:<30} Media: R$ {row['preco_unit_medio']:>7.2f}  "
                  f"Mediana: R$ {row['preco_unit_mediana']:>7.2f}  "
                  f"({int(row['qtd_anuncios'])} anuncios)")

    # 3e. Volume discount analysis (how price decreases with kit size)
    print(f"\n{'=' * 80}")
    print("  ANALISE DE DESCONTO POR VOLUME (preco unitario vs tamanho do kit)")
    print(f"  Excluindo: iluminadas/LED e personalizadas")
    print(f"{'=' * 80}")

    # Only non-personalized plain mochilas, EXCLUDING illuminated/LED
    is_illuminated = df_plain["titulo"].str.contains(
        r"(?i)iluminada|led|power\s*bank", regex=True
    )
    df_vol = df_plain[(df_plain["quantidade"] > 0) & (~is_illuminated)].copy()

    # Also exclude extreme outliers (unit price > R$500 = likely misclassified kit)
    outliers = df_vol[df_vol["preco_unitario"] > 500]
    if len(outliers) > 0:
        print(f"\n  Outliers removidos (unit > R$500, provavelmente kit nao detectado):")
        for _, row in outliers.iterrows():
            print(f"    - {row['titulo']}: R$ {row['preco_total']:.2f} (unit R$ {row['preco_unitario']:.2f})")
        df_vol = df_vol[df_vol["preco_unitario"] <= 500]

    vol_groups = df_vol.groupby("quantidade").agg(
        qtd_anuncios=("titulo", "count"),
        preco_unit_mediana=("preco_unitario", "median"),
        preco_unit_medio=("preco_unitario", "mean"),
        preco_unit_min=("preco_unitario", "min"),
        preco_unit_max=("preco_unitario", "max"),
    ).sort_index()
    vol_groups["preco_unit_mediana"] = vol_groups["preco_unit_mediana"].round(2)
    vol_groups["preco_unit_medio"] = vol_groups["preco_unit_medio"].round(2)

    print(f"\n  {'Qtd':<6} {'Anuncios':<10} {'Mediana':<12} {'Media':<12} {'Min':<12} {'Max':<12}")
    print(f"  {'-'*6} {'-'*10} {'-'*12} {'-'*12} {'-'*12} {'-'*12}")
    for qty_val, row in vol_groups.iterrows():
        print(f"  {qty_val:<6} {int(row['qtd_anuncios']):<10} "
              f"R$ {row['preco_unit_mediana']:<9.2f} "
              f"R$ {row['preco_unit_medio']:<9.2f} "
              f"R$ {row['preco_unit_min']:<9.2f} "
              f"R$ {row['preco_unit_max']:<9.2f}")

    # 3f. Illuminated/special products
    print(f"\n{'=' * 80}")
    print("  PRODUTOS ESPECIAIS (iluminada/LED)")
    print(f"{'=' * 80}")
    df_special = df[df["titulo"].str.contains(r"(?i)iluminada|led|power\s*bank", regex=True)]
    if len(df_special) > 0:
        for _, row in df_special.iterrows():
            print(f"  - {row['titulo']}")
            print(f"    R$ {row['preco_total']:.2f} (qty {row['quantidade']}, "
                  f"unit R$ {row['preco_unitario']:.2f})")
    else:
        print("  Nenhum produto especial encontrado.")

    # ===================================================================
    # 3g. ANALISE POR TIPO DE PRODUTO / CATEGORIAS DO TITULO
    # ===================================================================
    print(f"\n{'=' * 80}")
    print("  ANALISE POR TIPO DE PRODUTO")
    print(f"{'=' * 80}")

    tipo_stats = df.groupby("tipo_produto").agg(
        qtd_anuncios=("titulo", "count"),
        preco_unit_mediana=("preco_unitario", "median"),
        preco_unit_medio=("preco_unitario", "mean"),
        preco_unit_min=("preco_unitario", "min"),
        preco_unit_max=("preco_unitario", "max"),
    ).sort_values("qtd_anuncios", ascending=False)
    tipo_stats["preco_unit_mediana"] = tipo_stats["preco_unit_mediana"].round(2)
    tipo_stats["preco_unit_medio"] = tipo_stats["preco_unit_medio"].round(2)

    print(f"\n  {'Tipo':<30} {'Anuncios':<10} {'Mediana/un':<12} {'Media/un':<12} {'Min':<10} {'Max':<10}")
    print(f"  {'-'*30} {'-'*10} {'-'*12} {'-'*12} {'-'*10} {'-'*10}")
    for tipo, row in tipo_stats.iterrows():
        print(f"  {tipo:<30} {int(row['qtd_anuncios']):<10} "
              f"R$ {row['preco_unit_mediana']:<9.2f} "
              f"R$ {row['preco_unit_medio']:<9.2f} "
              f"R$ {row['preco_unit_min']:<7.2f} "
              f"R$ {row['preco_unit_max']:<7.2f}")

    # --- Quantidade de placas ---
    print(f"\n{'=' * 80}")
    print("  ANALISE POR QUANTIDADE DE PLACAS")
    print(f"{'=' * 80}")

    df_placas = df.copy()
    df_placas["qtd_placas_label"] = df_placas["qtd_placas"].apply(
        lambda x: f"{int(x)} placa(s)" if pd.notna(x) else "Nao especificado"
    )
    placas_stats = df_placas.groupby("qtd_placas_label").agg(
        qtd_anuncios=("titulo", "count"),
        preco_unit_mediana=("preco_unitario", "median"),
        preco_unit_medio=("preco_unitario", "mean"),
    ).sort_values("qtd_anuncios", ascending=False)
    placas_stats["preco_unit_mediana"] = placas_stats["preco_unit_mediana"].round(2)
    placas_stats["preco_unit_medio"] = placas_stats["preco_unit_medio"].round(2)

    print(f"\n  {'Placas':<20} {'Anuncios':<10} {'Mediana/un':<12} {'Media/un':<12}")
    print(f"  {'-'*20} {'-'*10} {'-'*12} {'-'*12}")
    for label, row in placas_stats.iterrows():
        print(f"  {label:<20} {int(row['qtd_anuncios']):<10} "
              f"R$ {row['preco_unit_mediana']:<9.2f} "
              f"R$ {row['preco_unit_medio']:<9.2f}")

    # --- Formato da placa ---
    print(f"\n{'=' * 80}")
    print("  ANALISE POR FORMATO DA PLACA")
    print(f"{'=' * 80}")

    df_formato = df.copy()
    df_formato["formato_label"] = df_formato["formato_placa"].fillna("Nao especificado")
    formato_stats = df_formato.groupby("formato_label").agg(
        qtd_anuncios=("titulo", "count"),
        preco_unit_mediana=("preco_unitario", "median"),
    ).sort_values("qtd_anuncios", ascending=False)
    formato_stats["preco_unit_mediana"] = formato_stats["preco_unit_mediana"].round(2)

    print(f"\n  {'Formato':<20} {'Anuncios':<10} {'Mediana/un':<12}")
    print(f"  {'-'*20} {'-'*10} {'-'*12}")
    for label, row in formato_stats.iterrows():
        print(f"  {label:<20} {int(row['qtd_anuncios']):<10} "
              f"R$ {row['preco_unit_mediana']:<9.2f}")

    # --- Tamanho ---
    df_tam = df[df["tamanho"].notna()].copy()
    if len(df_tam) > 0:
        print(f"\n{'=' * 80}")
        print("  TAMANHOS MENCIONADOS NOS TITULOS")
        print(f"{'=' * 80}")
        tam_stats = df_tam.groupby("tamanho").agg(
            qtd_anuncios=("titulo", "count"),
            preco_unit_mediana=("preco_unitario", "median"),
        ).sort_values("qtd_anuncios", ascending=False)
        tam_stats["preco_unit_mediana"] = tam_stats["preco_unit_mediana"].round(2)

        print(f"\n  {'Tamanho':<12} {'Anuncios':<10} {'Mediana/un':<12}")
        print(f"  {'-'*12} {'-'*10} {'-'*12}")
        for label, row in tam_stats.iterrows():
            print(f"  {label:<12} {int(row['qtd_anuncios']):<10} "
                  f"R$ {row['preco_unit_mediana']:<9.2f}")

    # --- Diferenciais ---
    df_dif = df[df["diferenciais"].notna()].copy()
    if len(df_dif) > 0:
        print(f"\n{'=' * 80}")
        print("  DIFERENCIAIS MENCIONADOS NOS TITULOS")
        print(f"{'=' * 80}")
        # Explode diferenciais (can have multiple per product)
        all_difs = []
        for _, row in df_dif.iterrows():
            for d in row["diferenciais"].split(", "):
                all_difs.append({"diferencial": d, "preco_unitario": row["preco_unitario"]})
        df_difs_exp = pd.DataFrame(all_difs)
        dif_stats = df_difs_exp.groupby("diferencial").agg(
            qtd_mencoes=("diferencial", "count"),
            preco_unit_mediana=("preco_unitario", "median"),
        ).sort_values("qtd_mencoes", ascending=False)
        dif_stats["preco_unit_mediana"] = dif_stats["preco_unit_mediana"].round(2)

        print(f"\n  {'Diferencial':<20} {'Mencoes':<10} {'Mediana/un':<12}")
        print(f"  {'-'*20} {'-'*10} {'-'*12}")
        for label, row in dif_stats.iterrows():
            print(f"  {label:<20} {int(row['qtd_mencoes']):<10} "
                  f"R$ {row['preco_unit_mediana']:<9.2f}")

    # --- Haste ---
    print(f"\n{'=' * 80}")
    print("  INCLUI HASTE?")
    print(f"{'=' * 80}")
    df_haste = df.copy()
    df_haste["haste_label"] = df_haste["inclui_haste"].fillna("Nao especificado")
    haste_stats = df_haste.groupby("haste_label").agg(
        qtd_anuncios=("titulo", "count"),
        preco_unit_mediana=("preco_unitario", "median"),
    ).sort_values("qtd_anuncios", ascending=False)
    haste_stats["preco_unit_mediana"] = haste_stats["preco_unit_mediana"].round(2)

    print(f"\n  {'Haste':<20} {'Anuncios':<10} {'Mediana/un':<12}")
    print(f"  {'-'*20} {'-'*10} {'-'*12}")
    for label, row in haste_stats.iterrows():
        print(f"  {label:<20} {int(row['qtd_anuncios']):<10} "
              f"R$ {row['preco_unit_mediana']:<9.2f}")

    # --- Summary ---
    print(f"\n{'=' * 80}")
    print("  RESUMO EXECUTIVO")
    print(f"{'=' * 80}")

    n_identified_sellers = len(seller_stats[seller_stats.index != "NAO IDENTIFICADO"])
    print(f"\n  Total de anuncios unicos relevantes: {len(df)}")
    print(f"  Vendedores identificados: {n_identified_sellers}")
    print(f"  Vendedores nao identificados: {int(seller_stats.loc['NAO IDENTIFICADO', 'qtd_anuncios']) if 'NAO IDENTIFICADO' in seller_stats.index else 0} anuncios")

    # Key price points (using clean data - no illuminated, no outliers)
    if len(df_plain_clean) > 0:
        p_median = df_plain_clean["preco_unitario"].median()
        p_mean = df_plain_clean["preco_unitario"].mean()
        p_mode_range = df["faixa_preco_unit"].mode()
        print(f"\n  Preco unitario (sem personalizacao, sem iluminadas/outliers):")
        print(f"    Mediana do mercado: R$ {p_median:.2f}")
        print(f"    Media do mercado:   R$ {p_mean:.2f}")
        if len(p_mode_range) > 0:
            print(f"    Faixa mais comum:   {p_mode_range.iloc[0]}")

    # Top 3 sellers
    top3 = seller_stats.head(3)
    print(f"\n  Top 3 vendedores por numero de anuncios:")
    for i, (seller, row) in enumerate(top3.iterrows(), 1):
        print(f"    {i}. {seller} ({int(row['qtd_anuncios'])} anuncios)")

    # Cheapest unit prices (non-personalized, identified sellers)
    if len(df_identified_plain) > 0:
        cheapest = df_identified_plain.nsmallest(5, "preco_unitario")[
            ["vendedor", "titulo", "quantidade", "preco_unitario", "preco_total"]
        ]
        print(f"\n  5 menores precos unitarios (sem personalizacao, vendedor identificado):")
        for _, row in cheapest.iterrows():
            print(f"    R$ {row['preco_unitario']:.2f}/un - {row['vendedor']} "
                  f"({row['titulo'][:60]}...)" if len(row['titulo']) > 60
                  else f"    R$ {row['preco_unitario']:.2f}/un - {row['vendedor']} "
                       f"({row['titulo']})")

    # ---------------------------------------------------------------------------
    # 5. SAVE TO EXCEL
    # ---------------------------------------------------------------------------
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "analise_concorrentes.xlsx")

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:

        # Sheet 1: All relevant products (with new classification columns)
        df_export = df.copy()
        df_export = df_export.sort_values(["vendedor", "preco_unitario"])
        col_order = [
            "vendedor", "titulo", "quantidade", "preco_unitario", "preco_total",
            "categoria_kit", "tipo_produto", "qtd_placas", "formato_placa",
            "tamanho", "inclui_haste", "diferenciais",
            "personalizada", "faixa_preco_unit", "pagina_orig"
        ]
        df_export[col_order].to_excel(writer, sheet_name="Produtos Relevantes", index=False)

        # Sheet 2: Seller summary
        seller_export = seller_stats.reset_index()
        seller_export.columns = [
            "Vendedor", "Qtd Anuncios", "Preco Unit Min", "Preco Unit Max",
            "Preco Unit Medio", "Preco Unit Mediana", "Preco Total Min", "Preco Total Max"
        ]
        seller_export.to_excel(writer, sheet_name="Vendedores", index=False)

        # Sheet 3: Category summary
        cat_export = cat_summary.reset_index()
        cat_export.columns = [
            "Categoria Kit", "Qtd Anuncios", "Preco Unit Min", "Preco Unit Max",
            "Preco Unit Medio", "Preco Unit Mediana"
        ]
        cat_export.to_excel(writer, sheet_name="Categorias Kit", index=False)

        # Sheet 4: Volume discount (with median)
        vol_export = vol_groups.reset_index()
        vol_export.columns = [
            "Quantidade", "Qtd Anuncios", "Preco Unit Mediana",
            "Preco Unit Medio", "Preco Unit Min", "Preco Unit Max"
        ]
        vol_export.to_excel(writer, sheet_name="Desconto Volume", index=False)

        # Sheet 5: Seller unit prices (non-personalized)
        if len(df_identified_plain) > 0:
            seller_unit_export = seller_unit.reset_index()
            seller_unit_export.columns = [
                "Vendedor", "Qtd Anuncios", "Preco Unit Medio",
                "Preco Unit Mediana", "Preco Unit Min", "Preco Unit Max"
            ]
            seller_unit_export.to_excel(
                writer, sheet_name="Vendedores Preco Unit", index=False
            )

        # Sheet 6: Non-relevant products
        if len(df_nonrel) > 0:
            df_nonrel.to_excel(writer, sheet_name="Nao Relevantes", index=False)

        # Sheet 7: Accessories
        if len(df_access) > 0:
            df_access.to_excel(writer, sheet_name="Acessorios", index=False)

        # Sheet 8: Price distribution
        price_dist_df = price_dist.reset_index()
        price_dist_df.columns = ["Faixa de Preco", "Qtd Anuncios"]
        price_dist_df.to_excel(writer, sheet_name="Distribuicao Precos", index=False)

        # Sheet 9: Tipo de Produto summary
        tipo_export = tipo_stats.reset_index()
        tipo_export.columns = [
            "Tipo Produto", "Qtd Anuncios", "Preco Unit Mediana",
            "Preco Unit Medio", "Preco Unit Min", "Preco Unit Max"
        ]
        tipo_export.to_excel(writer, sheet_name="Tipo Produto", index=False)

        # Sheet 10: Placas summary
        placas_export = placas_stats.reset_index()
        placas_export.columns = ["Qtd Placas", "Qtd Anuncios", "Preco Unit Mediana", "Preco Unit Medio"]
        placas_export.to_excel(writer, sheet_name="Qtd Placas", index=False)

        # Auto-adjust column widths
        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            for column_cells in ws.columns:
                max_length = 0
                col_letter = column_cells[0].column_letter
                for cell in column_cells:
                    try:
                        cell_len = len(str(cell.value)) if cell.value else 0
                        if cell_len > max_length:
                            max_length = cell_len
                    except Exception:
                        pass
                adjusted_width = min(max_length + 2, 60)
                ws.column_dimensions[col_letter].width = adjusted_width

    print(f"\n{'=' * 80}")
    print(f"  Arquivo salvo: {output_path}")
    print(f"  Abas: Produtos Relevantes, Vendedores, Categorias Kit,")
    print(f"        Desconto Volume, Vendedores Preco Unit, Nao Relevantes,")
    print(f"        Acessorios, Distribuicao Precos")
    print(f"{'=' * 80}")

    return df, seller_stats


if __name__ == "__main__":
    run_analysis()
