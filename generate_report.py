import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import configparser

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
        price_1m REAL,
        price_5m REAL,
        price_15m REAL,
        price_30m REAL,
        price_1h REAL,
        gain_1m REAL,
        gain_5m REAL,
        gain_15m REAL,
        gain_30m REAL,
        gain_1h REAL
    )
    ''')
    conn.commit()
    conn.close()

def create_report():
    """Gera relatório em Excel dos últimos X dias"""
    # Carregar configuração do arquivo config.ini
    config = configparser.ConfigParser()
    config.read('config.ini')
    days = int(config['Report']['days'])

    # Garantir que a tabela existe
    setup_database()
    
    conn = sqlite3.connect('contracts_report.db')
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        query = '''
        SELECT DISTINCT
            contract_address as "Contrato",
            detection_date as "Data",
            detection_time as "Hora",
            initial_price as "Preço Inicial",
            initial_mcap as "Market Cap Inicial",
            gain_1m as "Ganho 1min (%)",
            gain_5m as "Ganho 5min (%)",
            gain_15m as "Ganho 15min (%)",
            gain_30m as "Ganho 30min (%)",
            gain_1h as "Ganho 1h (%)"
        FROM contracts
        WHERE detection_date BETWEEN ? AND ?
        ORDER BY detection_date DESC, detection_time DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        
        if df.empty:
            print("Nenhum dado encontrado para o período especificado.")
            return
        
        # Remover duplicatas, se houver
        df = df.drop_duplicates(subset=['Contrato', 'Data', 'Hora'])
        
        # Formatar números
        df["Preço Inicial"] = df["Preço Inicial"].map('${:,.6f}'.format)
        df["Market Cap Inicial"] = df["Market Cap Inicial"].map('${:,.2f}'.format)
        for col in ["Ganho 1min (%)", "Ganho 5min (%)", "Ganho 15min (%)", "Ganho 30min (%)", "Ganho 1h (%)"]:
            df[col] = df[col].map('{:,.2f}%'.format)
        
        # Salvar relatório
        report_name = f'report_{datetime.now().strftime("%Y%m%d")}.xlsx'
        df.to_excel(report_name, index=False)
        print(f"Relatório gerado: {report_name}")
        
    except Exception as e:
        print(f"Erro ao gerar relatório: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_report() 