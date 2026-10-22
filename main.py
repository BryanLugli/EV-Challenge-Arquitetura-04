# =============================================================
#  GoodWe Smart Charging Station  -  Sprint 4 (FIAP)
#  Arquitetura de Computadores | Raspberry Pi Pico + MicroPython
#
#  ENTRADAS : botão CENÁRIO (GP16), botão TELA (GP17),
#             potenciômetro = energia manual (GP26/ADC0)
#  PROCESSO : gerenciador.distribuir_energia()
#  MEMÓRIA  : lista de veículos, histórico, byte de estados
#  SAÍDAS   : 9 LEDs (3 por EV), LCD 20x4 I2C, Monitor Serial
# =============================================================
from machine import Pin, ADC, I2C
import time
import gc
import gerenciador as ger
from lcd_i2c import LcdI2C

# ---------------- Configuração ----------------
CICLO_MS = 1000              # 1 ciclo de decisão por segundo
MIN_SIMULADOS = 5            # cada ciclo = 5 min de recarga simulada
ENERGIA_MAX_POT = 10000      # faixa do potenciômetro (W)
CENARIOS = (
    ("ALTA", 8000),          # Situação 1
    ("LIMITADA", 5000),      # Situação 2
    ("BAIXA", 2000),         # Situação 3
    ("MANUAL", None),        # energia definida no potenciômetro
)

# Dados iniciais dos veículos (MEMÓRIA: estrutura de dados da sessão)
DADOS_EV = (
    # num, modelo,     bateria %, solicitada W, capacidade Wh
    (1, "Compacto", 45, 2000, 40000),
    (2, "Sedan",    20, 2500, 60000),
    (3, "SUV",      70, 3000, 75000),
)

# ---------------- Hardware ----------------
PINOS_LED = ((2, 3, 4), (6, 7, 8), (10, 11, 12))   # (verde, amarelo, vermelho)
leds = [tuple(Pin(p, Pin.OUT) for p in trio) for trio in PINOS_LED]
pot = ADC(26)
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
lcd = LcdI2C(i2c, 0x27, 20, 4)


class Botao:
    """Leitura com debounce por software (detecta só a borda de descida)."""
    def __init__(self, gpio):
        self.pin = Pin(gpio, Pin.IN, Pin.PULL_UP)
        self.ultimo = 1
        self.t = 0

    def pressionado(self):
        v = self.pin.value()
        agora = time.ticks_ms()
        evento = False
        if v != self.ultimo and time.ticks_diff(agora, self.t) > 50:
            self.t = agora
            evento = (v == 0)
            self.ultimo = v
        return evento


btn_cenario = Botao(16)
btn_tela = Botao(17)

# ---------------- Estado do programa (memória RAM) ----------------
veiculos = []
historico = []          # últimas 10 decisões: (energia, byte de estados)
cache_lcd = [""] * 4
idx_cenario = 0
tela = 0
ciclos = 0


def iniciar_sessao():
    """Recarrega os dados iniciais: cada cenário começa igual (demo reproduzível)."""
    global veiculos
    veiculos = [ger.Veiculo(*d) for d in DADOS_EV]
    historico.clear()


def ler_energia():
    nome, valor = CENARIOS[idx_cenario]
    if valor is None:
        bruto = pot.read_u16()                       # 0..65535 (ADC 16 bits)
        valor = (bruto * ENERGIA_MAX_POT // 65535) // 100 * 100
    return valor


def atualizar_leds(piscar):
    for v, (verde, amarelo, vermelho) in zip(veiculos, leds):
        e = v.estado
        verde.value(1 if e == ger.ATIVA or (e == ger.COMPLETA and piscar) else 0)
        amarelo.value(1 if e == ger.REDUZIDA else 0)
        vermelho.value(1 if e == ger.ESPERA else 0)


def linha_ev(v):
    if v.estado == ger.COMPLETA:
        return "EV{} 100%  COMPLETA".format(v.num)
    return "EV{}{:>3}%{:>5}/{:<4} {}".format(
        v.num, int(v.bateria), v.alocada, v.solicitada, ger.ABREV[v.estado])


def montar_tela(energia, demanda, sobra, fila, codigo):
    nome = CENARIOS[idx_cenario][0]
    if tela == 0:      # resumo da estação
        return ["{:<8} DISP{:>6}W".format(nome, energia)] + \
               [linha_ev(v) for v in veiculos]
    if tela == 1:      # decisão do algoritmo
        alocado = sum(v.alocada for v in veiculos)
        prio = ">".join("EV{}".format(v.num) for v in fila)
        return ["DEMANDA: {:>6} W".format(demanda),
                "ALOCADO: {:>6} W".format(alocado),
                "SALDO:   {:>6} W".format(energia - demanda),
                "PRIO:" + (prio if prio else "-")]
    if tela == 2:      # representação de dados
        return ["DISP DEC: {}".format(energia),
                "HEX: 0x{:04X}".format(energia),
                "BIN: {:b}".format(energia),
                "EST: {:06b} 0x{:02X}".format(codigo, codigo)]
    # tela 3: memória / arquitetura
    entregue = sum(v.entregue_wh for v in veiculos) / 1000
    return ["RAM LIVRE:{:>8} B".format(gc.mem_free()),
            "CICLOS:{:>6} T+{:>3}m".format(ciclos, ciclos * MIN_SIMULADOS),
            "ENTREGUE:{:>7.1f}kWh".format(entregue),
            "I2C 0x27  SDA0 SCL1"]


def escrever_lcd(linhas):
    # Só reenvia pelo barramento I2C as linhas que mudaram
    for i, txt in enumerate(linhas):
        txt = (txt + " " * 20)[:20]
        if txt != cache_lcd[i]:
            lcd.move_to(0, i)
            lcd.putstr(txt)
            cache_lcd[i] = txt


def relatorio_serial(energia, demanda, sobra, fila, codigo):
    print("=" * 56)
    print("CENARIO: {} | ciclo {} | T+{} min".format(
        CENARIOS[idx_cenario][0], ciclos, ciclos * MIN_SIMULADOS))
    print("Energia disponivel: {} W | DEC {} | HEX 0x{:04X} | BIN {:b}".format(
        energia, energia, energia, energia))
    print("Demanda total: {} W | Saldo: {} W".format(demanda, energia - demanda))
    print("Prioridade (menor bateria primeiro): " +
          (" > ".join("EV{}".format(v.num) for v in fila) or "-"))
    print("-" * 56)
    for v in veiculos:
        print("EV{} {:<9} bat {:>5.1f}% | pede {:>4} W | recebe {:>4} W | {}".format(
            v.num, v.modelo, v.bateria, v.solicitada, v.alocada,
            ger.NOME_ESTADO[v.estado]))
    print("Byte de estados: 0b{:06b} (0x{:02X}) | RAM livre: {} B | historico: {}".format(
        codigo, codigo, gc.mem_free(), len(historico)))


# ---------------- Inicialização ----------------
escrever_lcd(["  GOODWE SMART", "  CHARGING STATION", "  FIAP - SPRINT 4", "  Iniciando..."])
print("GoodWe Smart Charging Station - Raspberry Pi Pico / MicroPython")
print("Botao AZUL = muda cenario | Botao VERDE = muda tela do LCD")
print("Cenario MANUAL: gire o potenciometro (0 a {} W)".format(ENERGIA_MAX_POT))
time.sleep_ms(1500)
iniciar_sessao()

ultimo_ciclo = time.ticks_ms()
energia_anterior = -1
piscar = False
forcar = True
dados = (0, 0, 0, [], 0)

# ---------------- Laço principal ----------------
while True:
    if btn_cenario.pressionado():
        idx_cenario = (idx_cenario + 1) % len(CENARIOS)
        iniciar_sessao()
        ciclos = 0
        forcar = True

    if btn_tela.pressionado():
        tela = (tela + 1) % 4
        escrever_lcd(montar_tela(*dados))

    agora = time.ticks_ms()
    if forcar or time.ticks_diff(agora, ultimo_ciclo) >= CICLO_MS:
        ultimo_ciclo = agora
        piscar = not piscar

        # 1) ENTRADA
        energia = ler_energia()
        # 2) PROCESSAMENTO
        demanda, sobra, fila = ger.distribuir_energia(energia, veiculos)
        codigo = ger.codificar_estados(veiculos)
        # 3) MEMÓRIA
        historico.append((energia, codigo))
        if len(historico) > 10:
            historico.pop(0)
        dados = (energia, demanda, sobra, fila, codigo)
        # 4) SAÍDA
        atualizar_leds(piscar)
        escrever_lcd(montar_tela(*dados))
        if forcar or energia != energia_anterior or ciclos % 5 == 0:
            relatorio_serial(*dados)

        energia_anterior = energia
        forcar = False
        ciclos += 1
        ger.avancar_tempo(veiculos, MIN_SIMULADOS)

    time.sleep_ms(20)
