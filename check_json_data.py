import os
import json
import pandas as pd
from datetime import datetime

# Caminhos dos arquivos
base_dir = os.path.dirname(os.path.abspath(__file__))
raw_dir = os.path.join(base_dir, "data/raw")
output_dir = os.path.join(base_dir, "data/processed")
os.makedirs(output_dir, exist_ok=True)

print(f"Verificando arquivos em: {raw_dir}")

# Função para processar e exibir um arquivo JSON
def process_json_file(file_path, output_prefix):
    print(f"\n=== Processando: {os.path.basename(file_path)} ===")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Salva uma versão formatada para visualização
        formatted_file = os.path.join(output_dir, f"{output_prefix}_formatted.json")
        with open(formatted_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Arquivo salvo em: {formatted_file}")
        
        # Exibe informações básicas sobre os dados
        if isinstance(data, dict):
            print("\nEstrutura do JSON:")
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    print(f"- {key}: {type(value).__name__} com {len(value)} itens")
                    
                    # Se for um dicionário, mostra as primeiras chaves
                    if isinstance(value, dict) and len(value) > 0:
                        sample_keys = list(value.keys())[:3]
                        print(f"  Amostra de chaves: {sample_keys}...")
                    # Se for uma lista, mostra o tipo do primeiro item
                    elif isinstance(value, list) and len(value) > 0:
                        first_item = value[0]
                        if isinstance(first_item, dict):
                            print(f"  Primeiro item chaves: {list(first_item.keys())}")
                            
                            # Se for a lista de moedas, mostra as primeiras 3
                            if 'id' in first_item and 'symbol' in first_item:
                                print("\nAmostra de moedas:")
                                for coin in value[:3]:
                                    print(f"  - {coin['id']} ({coin['symbol']}): {coin['name']}")
                                
                                # Cria um DataFrame para a lista de moedas
                                df = pd.DataFrame(value)
                                csv_path = os.path.join(output_dir, "coins_list.csv")
                                df.to_csv(csv_path, index=False)
                                print(f"\nLista completa de moedas salva em: {csv_path}")
                        
                        print(f"  Total de itens: {len(value)}")
                else:
                    print(f"- {key}: {value}")
            
            # Se for o arquivo de preços simples
            if 'bitcoin' in data and 'ethereum' in data:
                print("\nPreços atuais:")
                print(f"- Bitcoin (BTC): ${data['bitcoin']['usd']:,.2f}")
                print(f"- Ethereum (ETH): ${data['ethereum']['usd']:,.2f}")
                
                # Salva em CSV
                prices_df = pd.DataFrame([
                    {"moeda": "Bitcoin", "simbolo": "BTC", "preco_usd": data['bitcoin']['usd']},
                    {"moeda": "Ethereum", "simbolo": "ETH", "preco_usd": data['ethereum']['usd']}
                ])
                csv_path = os.path.join(output_dir, "prices.csv")
                prices_df.to_csv(csv_path, index=False)
                print(f"\nPreços salvos em: {csv_path}")
            
            # Se for um gráfico de mercado
            elif 'prices' in data and 'total_volumes' in data:
                # Processa preços
                prices = data.get('prices', [])
                if prices and len(prices) > 0:
                    timestamps = [pd.to_datetime(ts/1000, unit='s') for ts, _ in prices]
                    price_values = [price for _, price in prices]
                    
                    # Cria DataFrame com os preços
                    df_prices = pd.DataFrame({
                        'timestamp': timestamps,
                        'preco': price_values
                    })
                    
                    # Adiciona data e hora separadas
                    df_prices['data'] = df_prices['timestamp'].dt.date
                    df_prices['hora'] = df_prices['timestamp'].dt.time
                    
                    # Estatísticas básicas
                    print("\nEstatísticas de preços:")
                    print(f"- Período: {df_prices['timestamp'].min()} até {df_prices['timestamp'].max()}")
                    print(f"- Média: ${df_prices['preco'].mean():,.2f}")
                    print(f"- Mínimo: ${df_prices['preco'].min():,.2f}")
                    print(f"- Máximo: ${df_prices['preco'].max():,.2f}")
                    
                    # Salva em CSV
                    coin_name = os.path.basename(file_path).split('_')[2]  # Extrai o nome da moeda
                    csv_path = os.path.join(output_dir, f"{coin_name}_prices.csv")
                    df_prices.to_csv(csv_path, index=False)
                    print(f"\nDados de preços salvos em: {csv_path}")
                    
                    # Exibe as primeiras linhas
                    print("\nAmostra de preços:")
                    print(df_prices.head())
                
                # Processa volumes (se existir)
                volumes = data.get('total_volumes', [])
                if volumes and len(volumes) > 0:
                    # Similar ao processamento de preços
                    df_volumes = pd.DataFrame(volumes, columns=['timestamp', 'volume'])
                    df_volumes['timestamp'] = pd.to_datetime(df_volumes['timestamp']/1000, unit='s')
                    
                    # Salva em CSV
                    coin_name = os.path.basename(file_path).split('_')[2]
                    csv_path = os.path.join(output_dir, f"{coin_name}_volumes.csv")
                    df_volumes.to_csv(csv_path, index=False)
                    print(f"\nDados de volume salvos em: {csv_path}")
        
        return True
    except Exception as e:
        print(f"Erro ao processar o arquivo: {str(e)}")
        return False

# Processa todos os arquivos JSON no diretório raw
for filename in os.listdir(raw_dir):
    if filename.endswith('.json'):
        file_path = os.path.join(raw_dir, filename)
        output_prefix = os.path.splitext(filename)[0]
        process_json_file(file_path, output_prefix)

print("\n=== Processamento concluído ===")
print(f"Arquivos de saída salvos em: {output_dir}")
