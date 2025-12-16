import tkinter as tk
from tkinter import messagebox
import pandas as pd
import os
import openpyxl

# --- Lógica de Exportação para Excel ---

# (Mantenha as funções 'exportar_para_excel' e 'ao_clicar_ok' aqui)
def exportar_para_excel(cortes, tamanhos):
    """
    Cria um DataFrame do pandas com os dados e salva em um arquivo Excel.
    """
    try:
        data = {
            'Detalhe': ['Quantidade de Cortes', 'Quantidade de Tamanhos'],
            'Valor': [cortes, tamanhos]
        }
        df = pd.DataFrame(data)
        nome_arquivo = 'dados_exportados.xlsx'
        df.to_excel(nome_arquivo, index=False, sheet_name='Dados de Entrada')
        caminho_completo = os.path.abspath(nome_arquivo)
        
        messagebox.showinfo(
            "Sucesso!", 
            f"Dados exportados com sucesso para:\n{caminho_completo}"
        )

    except ValueError:
        messagebox.showerror("Erro de Valor", "As quantidades devem ser números inteiros válidos.")
    except Exception as e:
        messagebox.showerror("Erro de Exportação", f"Ocorreu um erro ao exportar: {e}")

def ao_clicar_ok():
    """
    Função chamada quando o botão 'OK' é pressionado.
    Lê os dados dos campos e chama a função de exportação.
    """
    try:
        cortes_str = entry_cortes.get()
        tamanhos_str = entry_tamanhos.get()
        tamanho_pp = entry_pp.get()
        tamanho_p = entry_p.get()
        tamanho_m = entry_m.get()
        tamanho_g = entry_g.get()
        tamanho_gg = entry_gg.get()
        
        # Garante que os campos não estão vazios antes de tentar converter
        if not cortes_str or not tamanhos_str:
             messagebox.showwarning("Atenção", "Por favor, preencha todos os campos.")
             return
             
        cortes = int(cortes_str)
        tamanhos = int(tamanhos_str)
        pp = int(tamanho_pp)
        p = int(tamanho_p)
        m = int(tamanho_m)
        g = int(tamanho_g)
        gg = int(tamanho_gg)

        exportar_para_excel(cortes, tamanhos, pp, p, m, g, gg)
        
    except ValueError:
        messagebox.showwarning("Atenção", "Por favor, insira números inteiros válidos em ambos os campos.")


# 1. Configuração da Janela Principal
root = tk.Tk()
root.title("Exportador de Dados para Excel")

# 2. Criação dos Rótulos (Labels)
label_pedido = tk.Label(root, text="QDigite o nome do pedido:")
label_cortes = tk.Label(root, text="Quantidade de Cortes:")
label_pp = tk.Label(root, text="PP")
label_p = tk.Label(root, text="P")
label_m = tk.Label(root, text="M")
label_g = tk.Label(root, text="G")
label_gg = tk.Label(root, text="GG")


# 3. Criação dos Campos de Entrada (Entries)
entry_cortes = tk.Entry(root, width=15)
entry_tamanhos = tk.Entry(root, width=15)
entry_pp = tk.Entry(root, width=15)
entry_p = tk.Entry(root, width=15)
entry_m = tk.Entry(root, width=15)
entry_g = tk.Entry(root, width=15)
entry_gg = tk.Entry(root, width=15)



# 4. Criação do Botão
button_ok = tk.Button(root, text="OK (Exportar Excel)", command=ao_clicar_ok)

# 5. Posicionamento dos Componentes (usando grid para organização)
label_cortes.grid(row=0, column=0, padx=10, pady=10, sticky='w')
entry_cortes.grid(row=0, column=1, padx=10, pady=10)
entry_pp.grid(row=0, column=1, padx=10, pady=10)
entry_p.grid(row=0, column=2, padx=5)
entry_m.grid(row=0, column=3, padx=5)
entry_g.grid(row=0, column=4, padx=5)
entry_gg.grid(row=0, column=5, padx=5)

label_pedido.grid(row=1, column=0, padx=10, pady=10, sticky='w')
entry_tamanhos.grid(row=1, column=1, padx=10, pady=10)
label_pp.grid(row=1, column=2, padx=5)
label_p.grid(row=1, column=3, padx=5)
label_m.grid(row=1, column=4, padx=5)
label_g.grid(row=1, column=5, padx=5)
label_gg.grid(row=1, column=6, padx=5)


button_ok.grid(row=2, column=0, columnspan=2, pady=15)

# 6. ESSENCIAL: Inicia o Loop Principal
root.mainloop()