# GoodWe Smart Charging Station – Sprint 4

Solução final da disciplina de **Arquitetura de Computadores** (FIAP – Ciência da Computação, turma 1CCPY).
Estação inteligente de recarga simulada no **Wokwi**, com **Raspberry Pi Pico** e **MicroPython**, que gerencia uma quantidade limitada de energia entre **3 veículos elétricos** conectados ao mesmo tempo. Inspirada no conceito do **GoodWe Smart Energy Controller**.

## Estrutura do repositório

| Arquivo | Função |
|---|---|
| `main.py` | Programa principal: lê entradas, chama o algoritmo, atualiza LEDs, LCD e Monitor Serial |
| `gerenciador.py` | Algoritmo de gerenciamento de energia (lógica pura, testável no PC) |
| `lcd_i2c.py` | Driver do LCD 20x4 via I2C (PCF8574, endereço `0x27`) |
| `diagram.json` | Circuito do Wokwi |

## Hardware simulado

| Componente | Pino do Pico | Papel |
|---|---|---|
| LCD 20x4 I2C | SDA = GP0, SCL = GP1 | Saída (comunicação I2C) |
| Botão azul **CENARIO** | GP16 (pull-up interno) | Entrada: Alta → Limitada → Baixa → Manual |
| Botão verde **TELA** | GP17 (pull-up interno) | Entrada: troca a tela do LCD |
| Potenciômetro | GP26 (ADC0) | Entrada: energia disponível no modo MANUAL (0–10.000 W) |
| EV1 – LEDs verde/amarelo/vermelho | GP2 / GP3 / GP4 | Saída |
| EV2 – LEDs verde/amarelo/vermelho | GP6 / GP7 / GP8 | Saída |
| EV3 – LEDs verde/amarelo/vermelho | GP10 / GP11 / GP12 | Saída |

Cada LED tem resistor de 220 Ω em série.

## Veículos simulados

| EV | Modelo | Bateria inicial | Potência solicitada | Capacidade |
|---|---|---|---|---|
| EV1 | Compacto | 45 % | 2.000 W | 40 kWh |
| EV2 | Sedan | 20 % | 2.500 W | 60 kWh |
| EV3 | SUV | 70 % | 3.000 W | 75 kWh |

Demanda total: **7.500 W**. Cada ciclo de 1 s representa 5 min de recarga, então a bateria sobe durante a simulação e a prioridade pode mudar sozinha.

## Algoritmo: prioridade por menor bateria com potência mínima garantida

1. **Energia ≥ demanda** → todos recebem o que pediram (LED verde).
2. **Energia < demanda** → os veículos são ordenados pela **menor bateria** (o mais descarregado é o mais urgente).
3. Seguindo essa fila, cada veículo recebe a **potência mínima de 1.400 W** enquanto houver energia. Quem não cabe fica **aguardando** (LED vermelho), porque carregadores AC não operam abaixo de ~6 A (≈1,4 kW).
4. A sobra é distribuída na mesma ordem de prioridade até completar o pedido de cada um.
5. Estado final: recebeu tudo → **verde**; recebeu parte → **amarelo**; recebeu nada → **vermelho**; bateria 100 % → **verde piscando** e a energia é liberada para os outros.

Por que essa estratégia: dividir igualmente poderia deixar todos abaixo do mínimo técnico (ninguém carrega). Garantir o mínimo e priorizar quem está mais descarregado atende primeiro quem mais precisa.

## Resultado das três situações

| Situação | Energia | EV1 (45 %) | EV2 (20 %) | EV3 (70 %) | Byte de estados |
|---|---|---|---|---|---|
| 1 – Alta | 8.000 W | 2.000 W 🟢 | 2.500 W 🟢 | 3.000 W 🟢 | `0b000000` (0x00) |
| 2 – Limitada | 5.000 W | 1.400 W 🟡 | 2.200 W 🟡 | 1.400 W 🟡 | `0b010101` (0x15) |
| 3 – Baixa | 2.000 W | 0 W 🔴 | 2.000 W 🟡 | 0 W 🔴 | `0b100110` (0x26) |
| Exemplo do enunciado | 6.000 W | 2.000 W 🟢 | 2.500 W 🟢 | 1.500 W 🟡 | `0b010000` (0x10) |

## Fluxo da arquitetura

```
ENTRADAS: botões (GP16/GP17), potenciômetro (ADC GP26), dados dos EVs
        │
        ▼
RASPBERRY PI PICO (RP2040, ARM Cortex-M0+ dual core, 264 KB SRAM)
        │  MicroPython
        ▼
PROCESSAMENTO: gerenciador.distribuir_energia()
        │
        ▼
MEMÓRIA: lista de objetos Veiculo + histórico das 10 últimas decisões
         + byte de estados (2 bits por EV)
        │
        ▼
SAÍDAS: 9 LEDs (GPIO) | LCD 20x4 (I2C) | Monitor Serial (USB/UART)
```

**Perguntas do enunciado:**

- **Quais dados entram?** Energia disponível (cenário fixo ou potenciômetro lido pelo ADC de 16 bits), bateria e potência solicitada de cada EV, e os comandos dos botões.
- **Como o Pico processa?** A cada 1 s o laço principal executa o algoritmo de distribuição no processador RP2040, interpretado pelo MicroPython.
- **Onde os dados ficam?** Na SRAM do Pico: lista `veiculos`, lista `historico` e a variável `codigo` (byte de estados). O código fica na memória flash.
- **Como decide?** Comparação demanda × disponibilidade, ordenação por bateria e alocação mínima + sobra (seção Algoritmo).
- **Quais saídas?** LEDs por veículo, LCD com 4 telas e relatório no Monitor Serial.

## Conceitos de Arquitetura de Computadores

| Conceito | Aplicação no projeto |
|---|---|
| Processador | RP2040 do Raspberry Pi Pico executa o algoritmo |
| Representação de dados | Energia, bateria e potência como inteiros/float; estados em 2 bits |
| Sistemas numéricos | Energia mostrada em decimal, hexadecimal e binário (LCD tela 3 e Serial) |
| Memória | Dados dos veículos, histórico e `gc.mem_free()` (RAM livre) na tela 4 |
| Entrada | Botões com pull-up e debounce por software; ADC do potenciômetro |
| Processamento | `distribuir_energia()` |
| Saída | GPIO para LEDs, LCD, Monitor Serial |
| Comunicação | I2C (LCD, endereço 0x27, modo 4 bits) e serial |
| Automação | Decisão automática a cada ciclo, sem intervenção do usuário |

### Exemplo de representação de dados

```
Energia disponível: 5000 W
Decimal:      5000
Hexadecimal:  0x1388
Binário:      1001110001000

Byte de estados na situação 3: 0b100110 = 0x26
  EV3 = 10 (aguardando) | EV2 = 01 (reduzida) | EV1 = 10 (aguardando)
```

O ADC do Pico devolve 0–65535 (16 bits), convertido em 0–10.000 W com resolução de 100 W.

## Telas do LCD (botão verde)

1. **Resumo:** cenário, energia disponível e cada EV (`EV1 45% 1400/2000 RD`)
2. **Decisão:** demanda, energia alocada, saldo e ordem de prioridade
3. **Dados:** energia em DEC/HEX/BIN e byte de estados
4. **Memória:** RAM livre, ciclos, tempo simulado, energia entregue, endereço I2C

Legenda: `OK` ativa, `RD` reduzida, `ES` espera, `CH` completa.

## Relação com o GoodWe Smart Energy Controller

O controlador da GoodWe monitora a energia disponível (rede, solar, bateria) e decide em tempo real como alimentar as cargas sem ultrapassar o limite da instalação. Nosso Pico faz o mesmo papel em escala educacional: mede a disponibilidade, compara com a demanda dos carregadores e redistribui a potência automaticamente quando a geração cai, evitando sobrecarga.

## Como executar

1. Abra o projeto no Wokwi (link do grupo) ou crie um projeto "Raspberry Pi Pico – MicroPython".
2. Substitua o `diagram.json` e adicione `main.py`, `gerenciador.py` e `lcd_i2c.py`.
3. Clique em **Start Simulation**.
4. Botão azul troca o cenário (reinicia as baterias); botão verde troca a tela; no modo MANUAL gire o potenciômetro.
