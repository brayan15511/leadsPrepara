import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import mysql.connector
import pandas as pd
import re

# Aqui eu me conecto ao BD (informações apenas de testes)
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="0000",
    database="escola_leads",
)
cursor = db.cursor()

def add_leads():
    nome = entry_nome.get()
    telefone = entry_telefone.get()
    idade = entry_idade.get()
    canal = combo_canal.get()
    situacao = combo_situacao.get()
    
    if not all([nome, telefone, idade, canal, situacao]):
        messagebox.showwarning("Atenção", "Todos os campos devem ser preenchidos!")
        return
    
    if not re.match(r'^\d+$', telefone):
        messagebox.showwarning("Atenção", "O telefone deve conter apenas dígitos.")
        return
    
    if not idade.isdigit():
        messagebox.showwarning("Atenção", "A idade deve ser um número.")
        return

    try:
        cursor.execute(
            "INSERT INTO leads (nome, telefone, idade, canal, situacao) VALUES (%s, %s, %s, %s, %s)",
            (nome, telefone, idade, canal, situacao),
        )
        db.commit()
        messagebox.showinfo("Sucesso", "Lead adicionado com sucesso!")
        limpar_campos()
        exibir_leads()
    except mysql.connector.Error as err:
        messagebox.showerror("Erro", f"Erro ao inserir o lead: {err}")

def limpar_campos():
    entry_nome.delete(0, tk.END)
    entry_telefone.delete(0, tk.END)
    entry_idade.delete(0, tk.END)
    combo_canal.set("")
    combo_situacao.set("")

def exibir_leads():
    for item in tree.get_children():
        tree.delete(item)

    pesquisa = entry_pesquisa.get()
    filtro_canal = combo_filtro_canal.get()
    filtro_situacao = combo_filtro_situacao.get()

    query = "SELECT * FROM leads WHERE 1=1"
    params = []

    if pesquisa:
        query += " AND (nome LIKE %s OR telefone LIKE %s)"
        params.append(f"%{pesquisa}%")
        params.append(f"%{pesquisa}%")
    
    if filtro_canal != "Todos":
        query += " AND canal = %s"
        params.append(filtro_canal)

    if filtro_situacao != "Todos":
        query += " AND situacao = %s"
        params.append(filtro_situacao)

    cursor.execute(query, params)
    for row in cursor.fetchall():
        row = list(row)  
        row[2] = formatar_numero(row[2])  
        tree.insert("", tk.END, values=row)

def editar_lead():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Atenção", "Selecione um lead para editar!")
        return
    item_values = tree.item(selected_item, "values")
    entry_nome.delete(0, tk.END)
    entry_nome.insert(0, item_values[1])
    entry_telefone.delete(0, tk.END)
    entry_telefone.insert(0, item_values[2])
    entry_idade.delete(0, tk.END)
    entry_idade.insert(0, item_values[3])
    combo_canal.set(item_values[4])
    combo_situacao.set(item_values[5])

    def confirmar_edicao():
        novo_nome = entry_nome.get()
        novo_telefone = entry_telefone.get()
        nova_idade = entry_idade.get()
        novo_canal = combo_canal.get()
        nova_situacao = combo_situacao.get()
        btn_confirmar_edicao.destroy() # << some com o botão de editar assim que ele for clicado

        if not all([novo_nome, novo_telefone, nova_idade, novo_canal, nova_situacao]):
            messagebox.showwarning("Atenção", "Todos os campos devem ser preenchidos!")
            return

        if not re.match(r'^\d+$', novo_telefone):
            messagebox.showwarning("Atenção", "O telefone deve conter apenas dígitos.")
            return

        if not nova_idade.isdigit():
            messagebox.showwarning("Atenção", "A idade deve ser um número.")
            return

        try:
            cursor.execute("""
                UPDATE leads
                SET nome = %s, telefone = %s, idade = %s, canal = %s, situacao = %s
                WHERE id = %s
            """, (novo_nome, novo_telefone, nova_idade, novo_canal, nova_situacao, item_values[0]))
            db.commit()
            messagebox.showinfo("Sucesso", "Lead atualizado com sucesso!")
            limpar_campos()
            exibir_leads()
        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Erro ao atualizar o lead: {err}")
    
    btn_confirmar_edicao = tk.Button(root, text="Confirmar Edição", command=confirmar_edicao, font=("Arial", 10, "bold"), borderwidth=2, relief="solid")
    btn_confirmar_edicao.grid(row=5, column=0, columnspan=2, padx=(290,0))


def excluir_lead():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Atenção", "Selecione um lead para excluir!")
        return
    item_values = tree.item(selected_item, "values")
    if messagebox.askyesno("Confirmação", f"Deseja realmente excluir o lead {item_values[1]}?"):
        try:
            cursor.execute("DELETE FROM leads WHERE id = %s", (item_values[0],))
            db.commit()
            messagebox.showinfo("Sucesso", "Lead excluído com sucesso!")
            exibir_leads()
        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Erro ao excluir o lead: {err}")

def formatar_numero(telefone):
    return re.sub(r'\D', '', telefone)  

def exportar_excel():
    pesquisa = entry_pesquisa.get()
    filtro_canal = combo_filtro_canal.get()
    filtro_situacao = combo_filtro_situacao.get()
    
    condicao_sql = " WHERE 1=1"
    params = []

    if pesquisa:
        condicao_sql += " AND (nome LIKE %s OR telefone LIKE %s)"
        params.extend([f"%{pesquisa}%", f"%{pesquisa}%"])

    if filtro_canal != "Todos":
        condicao_sql += " AND canal = %s"
        params.append(filtro_canal)

    if filtro_situacao != "Todos":
        condicao_sql += " AND situacao = %s"
        params.append(filtro_situacao)
    
    sql_query = "SELECT nome, telefone FROM leads" + condicao_sql
    cursor.execute(sql_query, params)
    results = cursor.fetchall()

    dados_exportacao = [
        {"Nome": row[0], "Telefone": formatar_numero(row[1])}
        for row in results
    ]

    df = pd.DataFrame(dados_exportacao, columns=["Nome", "Telefone"])

    file_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx")],
        title="Salvar Relatório de Leads"
    )

    if file_path:
        try:
            df.to_excel(file_path, index=False, header=False)
            messagebox.showinfo("Sucesso", "Relatório exportado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar para o Excel: {e}")

root = tk.Tk()
root.title("Sistema de Leads - Escola")
root.state("zoomed")

tk.Label(root, text="Nome:", font=("Arial", 20, "bold"), width=25).grid(row=0, column=0, padx=1, sticky="w")
entry_nome = tk.Entry(root, width=70, font=("Arial", 10, "bold"), borderwidth=2, relief="solid")
entry_nome.grid(row=0, column=0, padx=(275,0), sticky="w")


tk.Label(root, text="Telefone:", font=("Arial", 20, "bold"), width=25).grid(row=1, column=0, padx=5, sticky="w")
entry_telefone = tk.Entry(root, width=40, font=("Arial", 10, "bold"), borderwidth=2, relief="solid")
entry_telefone.grid(row=1, column=0, padx=(295,0), sticky="w")

tk.Label(root, text="Idade:", font=("Arial", 20, "bold"), width=25).grid(row=2, column=0, padx=5, sticky="w")
entry_idade = tk.Entry(root, width=10, font=("Arial", 10, "bold"), borderwidth=2, relief="solid")
entry_idade.grid(row=2, column=0, padx=(275,0), sticky="w")

tk.Label(root, text="Ações:", font=("Arial", 20, "bold"), width=25).grid(row=3, column=0, padx=5, sticky="w")
combo_canal = ttk.Combobox(root, values=["Jet", "Crédito", "Vagas", "Urna", "Indicação", "Outros"], width=40)
combo_canal.grid(row=3, column=0, padx=(275,0), sticky="w")

tk.Label(root, text="Situação:", font=("Arial", 20, "bold"), width=25).grid(row=4, column=0, padx=5, sticky="w")
combo_situacao = ttk.Combobox(root, values=["Encaminhado", "Não encaminhado", "Recusou encaminhamento", "Trabalhando"], width=40)
combo_situacao.grid(row=4, column=0, padx=(295,0), sticky="w")

frame_botoes = tk.Frame(root)
frame_botoes.grid(row=5, column=0, columnspan=2, pady=10, sticky="w")
btn_adicionar = tk.Button(frame_botoes, text="Adicionar Lead", command=add_leads, font=("Arial", 10, "bold"), borderwidth=2, relief="solid")
btn_adicionar.pack(side=tk.LEFT, padx=(150,0))
btn_editar = tk.Button(frame_botoes, text="Editar Lead", command=editar_lead, font=("Arial", 10, "bold"), borderwidth=2, relief="solid")
btn_editar.pack(side=tk.LEFT, padx=(150,0))
btn_excluir = tk.Button(frame_botoes, text="Excluir Lead", command=excluir_lead, font=("Arial", 10, "bold"), borderwidth=2, relief="solid")
btn_excluir.pack(side=tk.LEFT, padx=(150,0))

tk.Label(root, text="Pesquisar:", font=("Arial", 20, "bold"), width=25).grid(row=7, column=0, padx=5, sticky="w")
entry_pesquisa = tk.Entry(root, width=40, font=("Arial", 10, "bold"), borderwidth=2, relief="solid")
entry_pesquisa.grid(row=7, column=0, padx=(295,0), sticky="w")

btn_pesquisar = tk.Button(root, text="Pesquisar", width=15, command=exibir_leads, font=("Arial", 10, "bold"), borderwidth=2, relief="solid")
btn_pesquisar.grid(row=7, column=1, padx=(10, 0))

tk.Label(root, text="Filtrar por Ações:", font=("Arial", 20, "bold"), width=25).grid(row=8, column=0, padx=5, sticky="w")
combo_filtro_canal = ttk.Combobox(root, values=["Todos", "Jet", "Crédito", "Vagas", "Urna", "Indicação", "Outros"], width=40)
combo_filtro_canal.grid(row=8, column=0, padx=(345,0), sticky="w")
combo_filtro_canal.set("Todos")

tk.Label(root, text="Filtrar por Situação:", font=("Arial", 20, "bold"), width=25).grid(row=9, column=0, padx=5, sticky="w")
combo_filtro_situacao = ttk.Combobox(root, values=["Todos", "Encaminhado", "Não encaminhado", "Recusou encaminhamento", "Trabalhando"], width=40)
combo_filtro_situacao.grid(row=9, column=0, padx=(355,0), sticky="w")
combo_filtro_situacao.set("Todos")

btn_exportar = tk.Button(root, text="Exportar", width=15, command=exportar_excel, font=("Arial", 10, "bold"), borderwidth=2, relief="solid")
btn_exportar.grid(row=7, column=2, padx=(50,50), sticky="w")


tree = ttk.Treeview(root, columns=("ID", "Nome", "Telefone", "Idade", "Ações", "Situação", "Data Cadastro"), show="headings")
tree.heading("ID", text="ID")
tree.heading("Nome", text="Nome")
tree.heading("Telefone", text="Telefone") 
tree.heading("Idade", text="Idade")
tree.heading("Ações", text="Ações")
tree.heading("Situação", text="Situação")
tree.heading("Data Cadastro", text="Data Cadastro")
tree.grid(row=6, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")  # Tabela ocupa a largura total da janela

root.grid_rowconfigure(6, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

logo_image = Image.open(".\\img\\pC.png")
logo_image = logo_image.resize((300, 300))  # Ajuste o tamanho conforme necessário
logo_photo = ImageTk.PhotoImage(logo_image)
logo_label = tk.Label(root, image=logo_photo)
logo_label.grid(row=0, column=2, rowspan=5, padx=(0,220), pady=10, sticky="e")

exibir_leads()

root.mainloop()
