# =============================================================
#  gerenciador.py  -  Algoritmo de gerenciamento de energia
#  GoodWe Smart Charging Station (Sprint 4 - FIAP)
#
#  Lógica pura, sem acesso a hardware: pode ser testada no PC.
# =============================================================

# Potência mínima para manter uma recarga ativa (W).
# Referência: carregadores AC não operam abaixo de ~6 A (≈1,4 kW em 230 V).
P_MIN = 1400

# Estados codificados em 2 bits (cabem 3 veículos em 6 bits de um byte)
ATIVA = 0b00      # LED verde
REDUZIDA = 0b01   # LED amarelo
ESPERA = 0b10     # LED vermelho
COMPLETA = 0b11   # LED verde piscando (bateria 100%)

ABREV = ("OK", "RD", "ES", "CH")
NOME_ESTADO = ("RECARGA ATIVA", "RECARGA REDUZIDA", "AGUARDANDO", "COMPLETA")


class Veiculo:
    def __init__(self, num, modelo, bateria, solicitada, capacidade_wh):
        self.num = num                    # identificação (EV1, EV2, EV3)
        self.modelo = modelo
        self.bateria = float(bateria)     # % de carga
        self.solicitada = solicitada      # potência pedida (W)
        self.capacidade_wh = capacidade_wh
        self.alocada = 0                  # potência liberada pelo controlador (W)
        self.estado = ESPERA
        self.entregue_wh = 0.0            # energia entregue na sessão


def distribuir_energia(energia_disp, veiculos):
    """Distribui a energia disponível entre os veículos.

    Estratégia: PRIORIDADE POR MENOR BATERIA + POTÊNCIA MÍNIMA GARANTIDA
      1. Se a energia cobre toda a demanda -> todos recebem 100%.
      2. Senão, ordena a fila pela menor bateria (mais urgente primeiro).
      3. Cada veículo da fila recebe P_MIN enquanto houver energia;
         quem não couber fica em ESPERA (não faz sentido carregar
         abaixo do mínimo técnico).
      4. A sobra é entregue, na ordem de prioridade, até completar
         o que cada veículo pediu.
    Retorna (demanda_total, sobra, fila_de_prioridade).
    """
    for v in veiculos:
        v.alocada = 0
        if v.bateria >= 100:
            v.estado = COMPLETA

    ativos = [v for v in veiculos if v.bateria < 100]
    demanda = 0
    for v in ativos:
        demanda += v.solicitada

    fila = sorted(ativos, key=lambda v: (v.bateria, v.num))

    if demanda <= energia_disp:
        for v in ativos:
            v.alocada = v.solicitada
        sobra = energia_disp - demanda
    else:
        restante = energia_disp
        atendidos = []
        # Passo 3: garante o mínimo, por ordem de prioridade
        for v in fila:
            minimo = min(P_MIN, v.solicitada)
            if restante >= minimo:
                v.alocada = minimo
                restante -= minimo
                atendidos.append(v)
        # Passo 4: distribui a sobra por prioridade
        for v in atendidos:
            extra = min(v.solicitada - v.alocada, restante)
            v.alocada += extra
            restante -= extra
        sobra = restante

    for v in ativos:
        if v.alocada >= v.solicitada:
            v.estado = ATIVA
        elif v.alocada > 0:
            v.estado = REDUZIDA
        else:
            v.estado = ESPERA

    return demanda, sobra, fila


def codificar_estados(veiculos):
    """Empacota os estados em um único byte: EV1 = bits 1-0,
    EV2 = bits 3-2, EV3 = bits 5-4 (representação binária na memória)."""
    codigo = 0
    for i, v in enumerate(veiculos):
        codigo |= (v.estado & 0b11) << (2 * i)
    return codigo


def avancar_tempo(veiculos, minutos):
    """Simula a passagem do tempo: a bateria sobe conforme a potência alocada."""
    for v in veiculos:
        if v.alocada > 0 and v.bateria < 100:
            wh = v.alocada * minutos / 60
            v.entregue_wh += wh
            v.bateria = min(100.0, v.bateria + wh * 100 / v.capacidade_wh)
