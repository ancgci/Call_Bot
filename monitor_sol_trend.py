from telethon import TelegramClient, events
import re
import logging
import asyncio
import configparser
import winsound  # Importar a biblioteca para o som
import os
from datetime import datetime, timedelta
import sqlite3
import aiohttp

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar logging para arquivo e console
log_directory = 'logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

log_file = os.path.join(log_directory, f'monitor_{datetime.now().strftime("%Y%m%d")}.log')
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Carregar configurações do arquivo de configuração
config = configparser.ConfigParser()
config.read('config.ini')

# Insira suas credenciais da API do Telegram
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']
phone_number = config['Telegram']['phone_number']
bot_token = config['Bot']['token']
delay_between_sends = int(config['Settings']['delay_between_sends'])  # Ler o tempo de espera

session_name = 'monitor_sol_trend'

client = TelegramClient(session_name, api_id, api_hash)

# Expressão regular para identificar contratos
# Captura contratos logo após emojis, incluindo padrões específicos
contrato_pattern = r'(?:^|\n)(?:💊|💹)\s*([A-Za-z0-9]{32,44})\b'

# Cache com tempo de expiração para contratos
class ContractCache:
    def __init__(self, expiration_minutes=60):
        self.cache = {}
        self.expiration_minutes = expiration_minutes

    def add(self, contract, destination):
        self.cleanup()
        key = (contract, destination)
        self.cache[key] = datetime.now()

    def exists(self, contract, destination):
        self.cleanup()
        return (contract, destination) in self.cache

    def cleanup(self):
        now = datetime.now()
        expired = [k for k, v in self.cache.items() 
                  if now - v > timedelta(minutes=self.expiration_minutes)]
        for k in expired:
            del self.cache[k]

# Substituir os conjuntos por uma instância do ContractCache
contract_cache = ContractCache(expiration_minutes=60)

def validate_contract(contract):
    """Validação mais robusta de contratos"""
    if not (32 <= len(contract) <= 44):
        return False
    # Verificar se contém apenas caracteres válidos
    if not re.match(r'^[A-Za-z0-9]+$', contract):
        return False
    return True

async def send_trade_link(contract, destination):
    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            if not contract:
                logger.error("Tentativa de enviar contrato vazio")
                return False
            
            if not client.is_connected():
                logger.warning("Cliente desconectado. Tentando reconectar...")
                await client.connect()
            
            await client.send_message(destination, contract)
            logger.info(f"Contrato enviado ao {destination}: {contract}")
            winsound.Beep(900, 100)
            return True

        except Exception as e:
            logger.error(f"Tentativa {attempt + 1}/{max_retries} falhou: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Todas as tentativas falharam para {contract}")
                return False

def setup_database():
    """Configura o banco de dados SQLite"""
    conn = sqlite3.connect('contracts_report.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_address TEXT,
        detection_date TEXT,
        detection_time TEXT,
        initial_price REAL,
        initial_mcap REAL,
        price_10m REAL,
        price_30m REAL,
        price_1h REAL,
        gain_10m REAL,
        gain_30m REAL,
        gain_1h REAL
    )
    ''')
    conn.commit()
    conn.close()

async def get_token_info(contract_address):
    """Obtém informações do token via DEXScreener API"""
    url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('pairs'):
                        pair = data['pairs'][0]  # Pega o primeiro par
                        return {
                            'price': float(pair.get('priceUsd', 0)),
                            'mcap': float(pair.get('fdv', 0))
                        }
        except Exception as e:
            logger.error(f"Erro ao obter informações do token: {e}")
    return {'price': 0, 'mcap': 0}

async def schedule_price_updates(contract_address, detection_time):
    """Agenda atualizações de preço para diferentes intervalos"""
    try:
        delays = [
            (timedelta(minutes=10), 'price_10m', 'gain_10m'),
            (timedelta(minutes=30), 'price_30m', 'gain_30m'),
            (timedelta(hours=1), 'price_1h', 'gain_1h')
        ]
        
        initial_info = await get_token_info(contract_address)
        initial_price = initial_info['price']
        
        # Formatar data e hora como strings antes de inserir
        detection_date_str = detection_time.strftime('%Y-%m-%d')
        detection_time_str = detection_time.strftime('%H:%M:%S')
        
        conn = sqlite3.connect('contracts_report.db')
        cursor = conn.cursor()
        
        try:
            # Registra informações iniciais
            cursor.execute('''
            INSERT INTO contracts (
                contract_address, detection_date, detection_time, 
                initial_price, initial_mcap
            ) VALUES (?, ?, ?, ?, ?)
            ''', (
                contract_address,
                detection_date_str,
                detection_time_str,
                initial_price,
                initial_info['mcap']
            ))
            contract_id = cursor.lastrowid
            conn.commit()
            
            # Agenda atualizações
            for delay, price_field, gain_field in delays:
                try:
                    await asyncio.sleep(delay.total_seconds())
                    current_info = await get_token_info(contract_address)
                    current_price = current_info['price']
                    
                    if initial_price > 0 and current_price > 0:
                        gain_percentage = ((current_price - initial_price) / initial_price) * 100
                    else:
                        gain_percentage = 0
                    
                    cursor.execute(f'''
                    UPDATE contracts 
                    SET {price_field} = ?, {gain_field} = ?
                    WHERE id = ?
                    ''', (current_price, gain_percentage, contract_id))
                    conn.commit()
                except Exception as e:
                    logger.error(f"Erro ao atualizar preço após {delay}: {e}")
                    
        except Exception as e:
            logger.error(f"Erro ao inserir contrato no banco: {e}")
            conn.rollback()
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Erro geral no schedule_price_updates: {e}")

@client.on(events.NewMessage(chats=list(config['Origins'].values())))
async def handle_new_message(event):
    message = event.message.message
    logger.info(f"Nova mensagem recebida no canal:\n{message}")

    # Debug: imprimir a mensagem completa e tentar capturar o contrato de diferentes formas
    logger.info(f"Mensagem completa (debug): {repr(message)}")
    
    patterns = [
        r'(?:^|\n)(?:💊|💹)\s*([A-Za-z0-9]{32,44})\b',  # Padrão original
        r'(?:💊|💹)\s*([A-Za-z0-9]{32,44})\b',  # Sem restrição de início de linha
        r'\b([A-Za-z0-9]{32,44})\b',  # Captura qualquer contrato na mensagem
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, message)
        
        for contrato in matches:
            contrato = contrato.strip()
            
            if not validate_contract(contrato):
                logger.info(f"Contrato inválido: {contrato}")
                continue
            
            # Iniciar monitoramento de preço em background
            asyncio.create_task(schedule_price_updates(
                contrato,
                datetime.now()
            ))
            
            # Criar uma lista de tarefas para envio paralelo
            tasks = []
            for destination in config['Destinations'].values():
                if contract_cache.exists(contrato, destination):
                    logger.info(f"Contrato {contrato} já enviado para {destination}")
                    continue
                
                # Criar uma tarefa para cada destino
                tasks.append(asyncio.create_task(send_trade_link(contrato, destination)))
                
            # Aguardar todas as tarefas completarem
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Processar os resultados
                for i, (result, destination) in enumerate(zip(results, config['Destinations'].values())):
                    if isinstance(result, Exception):
                        logger.error(f"Erro ao enviar para {destination}: {result}")
                    elif result:
                        contract_cache.add(contrato, destination)
                        logger.info(f"Contrato enviado com sucesso para {destination}")
                
                # Aguardar o delay após o envio para todos os destinos
                await asyncio.sleep(delay_between_sends)

# Adicionar função para gerar relatório
async def generate_report(start_date=None, end_date=None):
    """Gera relatório de contratos e seus ganhos"""
    conn = sqlite3.connect('contracts_report.db')
    cursor = conn.cursor()
    
    query = '''
    SELECT 
        contract_address,
        detection_date,
        detection_time,
        initial_price,
        initial_mcap,
        gain_10m,
        gain_30m,
        gain_1h
    FROM contracts
    '''
    
    if start_date and end_date:
        query += ' WHERE detection_date BETWEEN ? AND ?'
        cursor.execute(query, (start_date, end_date))
    else:
        cursor.execute(query)
    
    results = cursor.fetchall()
    conn.close()
    
    return results

async def main():
    try:
        setup_database()
        await client.start(phone=phone_number)
        logger.info("Monitorando mensagens do canal...")
        
        try:
            await client.run_until_disconnected()
        except asyncio.CancelledError:
            logger.info("Cliente desconectado normalmente")
        except Exception as e:
            logger.error(f"Erro durante execução do cliente: {e}")
            
    except Exception as e:
        logger.error(f"Erro ao iniciar o cliente: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()
        logger.info("Cliente finalizado")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Programa encerrado pelo usuário")
    except Exception as e:
        logger.error(f"Erro não tratado: {e}")