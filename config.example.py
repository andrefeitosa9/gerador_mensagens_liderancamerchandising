"""Configurações do Gerador de Mensagens - Merchandising

- Copie este arquivo para config.py e ajuste conforme necessário.
- Por padrão, o projeto tenta reutilizar o DB_CONFIG do gerador_mensagens_ruptura/config.py.
"""

# Configurações do Banco de Dados (SQL Server)
DB_CONFIG = {
    "server": "192.168.1.18",
    "database": "rbdistrib_Trade",
    "username": "USUARIO_AQUI",
    "password": "SENHA_AQUI",
    "driver": "SQL Server",
}

# Regras de data
# weekday(): 0=segunda ... 6=domingo
# segunda -> usa sábado como "ontem" (offset=2)
# terça..sábado -> usa ontem (offset=1)
DIAS_OFFSET = {
    0: 2,
    1: 1,
    2: 1,
    3: 1,
    4: 1,
    5: 1,
    6: 1,
}

# Tabelas
TABLE_AREA_MERCHAN = "Rbdistrib_Trade.dbo.dimAreaMerchan"
TABLE_TELEFONE_LIDERANCA = "Rbdistrib_Trade.dbo.dimTelefoneMerchanLideranca"
TABLE_MONITORAMENTO = "Monitoramento_Promotor"  # normalmente já está no rbdistrib_Trade

# Valores que contam como visita feita
CHECKIN_VALIDOS = ("Manual", "Manual e GPS")

# Ordem preferencial das áreas (para o líder geral)
AREAS_ORDEM_PADRAO = ["Centro Norte", "Filial", "Grandes Redes", "Trad"]

# Telefones
USE_TEST_PHONE = True
TEST_PHONE_E164 = "+5585986068742"  # +55 + DDD + número (E.164)

# Envio
# True = apenas imprime mensagens (não abre WhatsApp)
MODO_TESTE = True
