# Gerador de Mensagens (Merchandising) – WhatsApp

Gera e envia via WhatsApp Web um resumo diário de **aderência ao roteiro** para líderes do Merchandising.

## Regras

- Envio somente **segunda a sábado** (domingo não envia)
- Na **segunda-feira**, o “Ontem” considera **sábado**
- Líder geral (área = `Merchan`) recebe:
  - Aderência geral (Ontem e Mês)
  - Aderência por área (Ontem e Mês)
  - Na segunda, recebe também o bloco de **Grupos/Redes importantes (mês)**
- Líderes de área recebem:
  - Aderência da área (Ontem e Mês)
  - Colaboradores da área (ordem alfabética) com Ontem e Mês

## Pré-requisitos

- Windows com WhatsApp Web funcionando no navegador padrão
- Python instalado e no PATH
- Driver ODBC para SQL Server instalado (ex.: "SQL Server" / "ODBC Driver 17 for SQL Server")

## Instalação

```bat
cd "B:\Trade\Compartilhado\Inteligência de Mercado\Scripts\gerador_mensagens_liderancamerchandising"
python -m pip install -r requirements.txt
```

## Configuração

Este projeto tenta **reutilizar** as credenciais do projeto de ruptura automaticamente.

- Para testar enviando tudo para um único número:
  - Ajuste `USE_TEST_PHONE = True` em `config.py` (use `config.example.py` como base)
  - Ajuste `TEST_PHONE_E164` para o número desejado

- Para rodar em produção (usar telefones do banco):
  - `USE_TEST_PHONE = False`

> Importante: `config.py` é ignorado no git (contém credenciais/config sensível).

## Rodar (simulação)

Não abre o WhatsApp; apenas imprime as mensagens no terminal.

```bat
python main.py
```

## Rodar (envio real)

Abre o WhatsApp Web e envia mensagens.

```bat
python main.py --enviar
```

## Agendamento (Task Scheduler)

Use o arquivo `run.bat` deste diretório.

- Ação: Start a program
- Program/script: caminho completo do `run.bat`
- Start in: a pasta do projeto

Dica: execute manualmente uma vez para garantir que o WhatsApp Web está logado.
