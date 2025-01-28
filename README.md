# Monitor SOL Trend Bot

## Descrição

Bot desenvolvido para monitorar canais do Telegram e encaminhar automaticamente contratos da Solana (SOL) para bots de destino. O sistema também monitora e registra o desempenho dos tokens ao longo do tempo.

## Funcionalidades Principais

- ✅ Monitoramento em tempo real de canais Telegram
- ✅ Detecção automática de contratos SOL
- ✅ Envio simultâneo para múltiplos bots
- ✅ Sistema anti-duplicação
- ✅ Notificação sonora
- ✅ Logs detalhados
- ✅ Tracking de preços e market cap
- ✅ Relatórios de performance dos tokens

## Requisitos

- Python 3.7 ou superior
- Conta Telegram
- Credenciais de API do Telegram (api_id e api_hash)

## Instalação

1. Preparação inicial:
   - Desinstale o Python completamente do seu sistema
   - Baixe e instale especificamente o Python 3.10.11 (versão estável): 
     https://www.python.org/downloads/release/python-31011/
   - Escolha o instalador Windows (64-bit)
   - Durante a instalação:
     - Marque "Add Python 3.10 to PATH"
     - Marque "Install pip"
     - Escolha "Customize installation"
     - Marque todas as opções opcionais
     - Instale para todos os usuários

2. Verifique a instalação (no Prompt de Comando como Administrador):
```bash
# Verifique a versão do Python (deve mostrar 3.10.x)
python --version

# Instale/Atualize o pip globalmente
python -m ensurepip --default-pip
python -m pip install --upgrade pip
```

3. Configure o projeto:
```bash
# Remova ambiente virtual antigo
rd /s /q .venv

# Crie novo ambiente virtual
python -m venv .venv --clear

# Ative o ambiente virtual
# No PowerShell:
.\.venv\Scripts\Activate.ps1
# OU no Prompt de Comando (CMD):
.venv\Scripts\activate.bat
# OU no Git Bash:
source .venv/Scripts/activate

# Instale pip no ambiente virtual
python -m ensurepip --default-pip
python -m pip install --upgrade pip

# Instale as dependências
python -m pip install --no-cache-dir telethon
python -m pip install --no-cache-dir requests
python -m pip install --no-cache-dir configparser
python -m pip install --no-cache-dir aiohttp
python -m pip install --no-cache-dir pandas
python -m pip install --no-cache-dir openpyxl
```

4. Teste a instalação:
```bash
# Verifique se as dependências foram instaladas
python -m pip list
```

## Configuração

1. Crie um arquivo `config.ini` com a seguinte estrutura:
```ini
[Telegram]
api_id = seu_api_id
api_hash = seu_api_hash
phone_number = seu_numero_telefone

[Bot]
token = seu_token_bot

[Settings]
delay_between_sends = 1

[Origins]
origin1 = @canal_origem1
origin2 = @canal_origem2

[Destinations]
destination1 = @bot_destino1
destination2 = @bot_destino2
```

2. Obtenha suas credenciais:
   - Acesse https://my.telegram.org
   - Crie uma aplicação para obter api_id e api_hash
   - Configure os canais de origem e bots de destino no config.ini

## Como Usar

1. Execute o bot:
```bash
python monitor_sol_trend.py
```

2. Na primeira execução:
   - Faça login com seu número de telefone
   - Insira o código de verificação recebido

3. O bot começará a monitorar automaticamente

## Sistema de Reports

O bot inclui um sistema de tracking e relatórios que monitora:
- Preço inicial e Market Cap do token
- Variação de preço em 10 minutos
- Variação de preço em 30 minutos
- Variação de preço em 1 hora

### Gerando Relatórios

Para gerar um relatório dos últimos 7 dias:
```bash
python generate_report.py
```

O relatório será salvo em formato Excel com:
- Data e hora de detecção
- Preço inicial e Market Cap
- Ganhos percentuais nos intervalos
- Ordenação por data/hora mais recente

## Funcionamento

- Monitora mensagens nos canais de origem
- Detecta contratos após emojis específicos (💊 ou 💹)
- Valida o formato do contrato
- Encaminha simultaneamente para todos os bots configurados
- Rastreia preços via DEXScreener API
- Gera relatórios de performance

## Logs

- Salvos na pasta `logs/`
- Formato: `monitor_YYYYMMDD.log`
- Registra todas as operações e erros

## Dicas

- Mantenha o arquivo config.ini atualizado
- Monitore os logs regularmente
- Verifique os relatórios diariamente
- Ajuste o delay_between_sends conforme necessário

## Segurança

- Nunca compartilhe suas credenciais de API
- Mantenha o config.ini em local seguro
- Use apenas em canais e bots confiáveis

## Limitações

- Funciona apenas com contratos da Solana
- Requer conexão estável com internet
- Necessita de sessão Telegram ativa
- Tracking depende da disponibilidade da DEXScreener API

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir melhorias
- Enviar pull requests

