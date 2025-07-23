import os
import json
import sys

def main():
    # Caminhos
    base_path = "/data/raw"
    
    # Encontra o arquivo mais recente da lista de moedas
    coins_files = [f for f in os.listdir(base_path) if f.startswith('coins_list_') and f.endswith('.json')]
    if not coins_files:
        print("Nenhum arquivo de lista de moedas encontrado!")
        sys.exit(1)
    
    latest_file = max(coins_files, key=lambda x: os.path.getmtime(os.path.join(base_path, x)))
    file_path = os.path.join(base_path, latest_file)
    
    print(f"Analisando arquivo: {file_path}")
    print("-" * 80)
    
    # Lê o conteúdo do arquivo
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Tenta carregar como JSON
        data = json.loads(content)
        
        # Verifica o tipo de dados
        print(f"Tipo do dado principal: {type(data)}")
        
        if isinstance(data, list):
            print(f"\nÉ uma lista com {len(data)} itens")
            if data:
                print("\nPrimeiro item:")
                print(json.dumps(data[0], indent=2))
                
                # Verifica as chaves do primeiro item
                print("\nChaves do primeiro item:")
                for key in data[0].keys():
                    print(f"- {key}: {type(data[0][key])} = {data[0][key]}")
                
        elif isinstance(data, dict):
            print("\nÉ um dicionário com chaves:")
            for key in data.keys():
                print(f"- {key}: {type(data[key])}")
                
                # Se o valor for uma lista, mostra o primeiro item
                if isinstance(data[key], list) and data[key]:
                    print(f"  Primeiro item: {data[key][0]}")
        
        # Verifica o tamanho do arquivo
        file_size = os.path.getsize(file_path)
        print(f"\nTamanho do arquivo: {file_size} bytes")
        
        # Conta o número de linhas
        with open(file_path, 'r') as f:
            line_count = sum(1 for _ in f)
        print(f"Número de linhas: {line_count}")
        
        # Verifica se o arquivo tem uma única linha (possível JSON em uma linha)
        if line_count == 1:
            print("\nAVISO: O arquivo tem apenas uma linha. Pode ser um JSON em uma única linha.")
            
            # Conta o número de itens se for uma lista
            if isinstance(data, list):
                print(f"Número de itens na lista: {len(data)}")
                
        # Mostra os primeiros 200 caracteres do arquivo
        print("\nPrimeiros 200 caracteres do arquivo:")
        with open(file_path, 'r') as f:
            print(f.read(200) + "...")
        
    except Exception as e:
        print(f"Erro ao processar o arquivo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
