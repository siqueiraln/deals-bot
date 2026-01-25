import os

def fix_env():
    try:
        with open(".env", "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        new_lines = []
        for line in lines:
            if line.startswith("ML_COOKIES="):
                # Extrai valor bruto
                try:
                    key, val = line.split("=", 1)
                except ValueError:
                    new_lines.append(line)
                    continue

                val = val.strip()
                
                # Remove o comentário sufixo gerado pelo editor/template
                if "# Cole seus cookies" in val:
                    val = val.split("# Cole seus cookies")[0].strip()
                
                # Remove aspas externas existentes para garantir limpeza
                # (Assumindo que o usuário não usou aspas ou usou errado)
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                elif val.startswith("'") and val.endswith("'"):
                    val = val[1:-1]
                
                # Envolve em aspas simples (seguro para JSON com aspas duplas)
                new_lines.append(f"ML_COOKIES='{val}'\n")
                print("✅ ML_COOKIES formatado e limpo.")
            else:
                new_lines.append(line)
        
        with open(".env", "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            
    except Exception as e:
        print(f"❌ Erro ao corrigir .env: {e}")

if __name__ == "__main__":
    fix_env()
