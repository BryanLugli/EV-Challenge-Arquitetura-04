# Roteiro do vídeo (máx. 5 min)

| Tempo | Quem | O que mostrar / falar |
|---|---|---|
| 0:00–0:25 | Integrante 1 | Apresentação do grupo e do objetivo: estação inteligente que divide energia limitada entre 3 EVs, inspirada no GoodWe Smart Energy Controller. |
| 0:25–1:00 | Integrante 1 | Circuito no Wokwi: Pico no centro, LCD I2C (GP0/GP1), 2 botões, potenciômetro (ADC), 3 grupos de LEDs com resistores. Explicar entradas e saídas. |
| 1:00–1:45 | Integrante 2 | Código: `gerenciador.py`. Explicar o algoritmo: ordena pela menor bateria, garante 1.400 W mínimos, distribui a sobra. Por que não dividir igualmente. |
| 1:45–2:15 | Integrante 2 | Iniciar simulação. **Situação 1 (8.000 W):** todos verdes, LCD e Serial mostram 7.500 W de demanda e +500 W de saldo. |
| 2:15–2:50 | Integrante 3 | Botão azul. **Situação 2 (5.000 W):** todos amarelos. Mostrar EV2 recebendo 2.200 W por ter menos bateria. Botão verde → tela de decisão (prioridade EV2>EV1>EV3). |
| 2:50–3:20 | Integrante 3 | Botão azul. **Situação 3 (2.000 W):** só EV2 carrega (amarelo), EV1 e EV3 vermelhos. |
| 3:20–3:50 | Integrante 1 | Botão azul → MANUAL. Girar potenciômetro: mostrar LEDs mudando em tempo real (ex.: 6.000 W → EV1 e EV2 verdes, EV3 amarelo). |
| 3:50–4:30 | Integrante 2 | Tela de dados: 5000 = 0x1388 = 1001110001000; byte de estados 0b100110 = 0x26 (2 bits por EV). Tela de memória: RAM livre, histórico na SRAM, I2C 0x27. |
| 4:30–5:00 | Integrante 3 | Tabela de conceitos (processador, memória, E/S, comunicação, automação) e fechamento com a relação com a GoodWe. |

Dica: deixe o Monitor Serial visível ao lado do circuito durante toda a gravação.
