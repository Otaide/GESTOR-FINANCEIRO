import tkinter as tk
from tkinter import ttk, messagebox
try:
    from tkcalendar import Calendar, DateEntry
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tkcalendar"])
    from tkcalendar import Calendar, DateEntry
from datetime import datetime
import sqlite3
import csv

class DatabaseManager:
    def __init__(self, db_name="financeiro.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._initialize_database()

    def _initialize_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS movimentacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                tipo TEXT NOT NULL,
                conta TEXT NOT NULL,
                valor REAL NOT NULL,
                observacoes TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS contas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def execute_query(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Erro no Banco de Dados", str(e))

    def fetch_all(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def adicionar_movimentacao(self, **kwargs):
        # Validar formato da data antes de inserir
        try:
            datetime.strptime(kwargs['data'], "%d/%m/%Y")
        except ValueError:
            raise ValueError("Formato de data inválido. Use DD/MM/AAAA")
        query = '''INSERT INTO movimentacoes (data, tipo, conta, valor, observacoes)
                   VALUES (:data, :tipo, :conta, :valor, :observacoes)'''
        self.execute_query(query, kwargs)

    def editar_movimentacao(self, id, **kwargs):
        query = '''UPDATE movimentacoes
                   SET data=:data, tipo=:tipo, conta=:conta, valor=:valor, observacoes=:observacoes
                   WHERE id=:id'''
        self.execute_query(query, {**kwargs, "id": id})

    def excluir_movimentacao(self, id):
        query = 'DELETE FROM movimentacoes WHERE id=?'
        self.execute_query(query, (id,))

    def buscar_movimentacoes(self, filtro=None):
        if filtro:
            return self.fetch_all('SELECT * FROM movimentacoes WHERE conta=?', (filtro,))
        return self.fetch_all('SELECT * FROM movimentacoes')

    def buscar_contas(self):
        return self.fetch_all('SELECT nome FROM contas')

    def adicionar_conta(self, nome):
        query = 'INSERT INTO contas (nome) VALUES (?)'
        self.execute_query(query, (nome,))

    def excluir_conta(self, nome):
        query = 'DELETE FROM contas WHERE nome=?'
        self.execute_query(query, (nome,))

    def calcular_total(self, tipo):
        query = f'SELECT SUM(valor) FROM movimentacoes WHERE tipo=?'
        result = self.fetch_all(query, (tipo,))
        return result[0][0] or 0.0

    def calcular_saldo(self):
        entradas = self.calcular_total("Entrada")
        saidas = self.calcular_total("Saída")
        return entradas - saidas

    def exportar_csv(self, filename="movimentacoes.csv"):
        try:
            data = self.fetch_all('SELECT data, tipo, conta, valor, observacoes FROM movimentacoes')
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Data", "Tipo", "Conta", "Valor", "Observações"])
                writer.writerows(data)
            messagebox.showinfo("Exportação", f"Dados exportados com sucesso para {filename}")
        except Exception as e:
            messagebox.showerror("Erro na Exportação", str(e))

class UIManager:
    def __init__(self, root):
        self.db_manager = DatabaseManager()
        self.root = root
        self.root.title("Gestão Financeira")
        self.root.geometry("900x700")
        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Paleta de cores empresariais
        primary_color = "#2c3e50"  # Azul escuro
        secondary_color = "#ecf0f1"  # Cinza claro
        accent_color = "#3498db"  # Azul
        text_color = "#ffffff"  # Branco
        background_color = "#34495e"  # Cinza escuro
        hover_color = "#2980b9"  # Azul mais claro para hover
        border_color = "#bdc3c7"  # Cinza para bordas
        shadow_color = "#95a5a6"  # Cinza para sombras

        # Configuração de estilos
        style.configure("TLabel", font=("Arial", 12), background=background_color, foreground=text_color)
        style.configure("Resumo.TLabel", font=("Arial", 12), background="#1abc9c", foreground=text_color)  # Verde
        style.configure("Movimentacao.TLabel", font=("Arial", 12), background="#bdc3c7", foreground=primary_color)  # Cinza
        style.configure("TButton", font=("Arial", 12), padding=5, background=primary_color, foreground=text_color, bordercolor=border_color)
        style.configure("TEntry", font=("Arial", 12), background=secondary_color, foreground=primary_color, bordercolor=border_color)
        style.configure("TCombobox", font=("Arial", 12), background=secondary_color, foreground=primary_color, bordercolor=border_color)
        style.configure("Treeview", font=("Arial", 12), background=secondary_color, foreground=primary_color, fieldbackground=secondary_color, bordercolor=border_color)
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background=primary_color, foreground=text_color, bordercolor=border_color)
        style.configure("TNotebook", background=background_color, bordercolor=border_color)
        style.configure("TNotebook.Tab", font=("Arial", 12), bordercolor=border_color)
        style.map("TNotebook.Tab", background=[("selected", "#1abc9c"), ("!selected", primary_color)], foreground=[("selected", text_color), ("!selected", text_color)])
        style.configure("Resumo.TFrame", background="#1abc9c")  # Verde
        style.configure("Movimentacao.TFrame", background="#bdc3c7")  # Cinza
        style.map("TButton", background=[("active", hover_color)], bordercolor=[("active", border_color)], shadow=[("active", shadow_color)])
        style.map("Treeview.Heading", background=[("!active", primary_color)], foreground=[("!active", text_color)])

        # Aplicar cores de fundo ao root
        self.root.configure(background=background_color)

    def _build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.frame_resumo = ttk.Frame(self.notebook)
        self.frame_movimentacao = ttk.Frame(self.notebook)

        self.notebook.add(self.frame_resumo, text="Resumo Financeiro")
        self.notebook.add(self.frame_movimentacao, text="Movimentação")

        self._build_resumo_ui()
        self._build_movimentacao_ui()

        self.root.bind("<Escape>", self._limpar_filtros_movimentacao)

    def _build_resumo_ui(self):
        frame_top = ttk.Frame(self.frame_resumo, style="Resumo.TFrame")
        frame_top.pack(fill="x", padx=10, pady=10)

        self.label_saldo_total = ttk.Label(frame_top, text="Saldo Total: R$ 0.00", font=("Arial", 16), style="Resumo.TLabel")
        self.label_saldo_total.pack(side="left", padx=10)

        self.tree_resumo = ttk.Treeview(self.frame_resumo, columns=("Conta", "Valor"), show="headings")
        for col in self.tree_resumo["columns"]:
            self.tree_resumo.heading(col, text=col)
            self.tree_resumo.column(col, width=150)
        self.tree_resumo.pack(fill="both", expand=True, padx=10, pady=10)

        self._atualizar_resumo()

    def _abrir_filtros(self):
        self.filtros_toplevel = tk.Toplevel(self.root)
        self.filtros_toplevel.title("Filtros")
        self.filtros_toplevel.geometry("400x200")
        self.filtros_toplevel.transient(self.root)
        self.filtros_toplevel.grab_set()

        ttk.Label(self.filtros_toplevel, text="Período:").grid(row=0, column=0, padx=10, pady=10)
        self.entry_data_inicio = DateEntry(self.filtros_toplevel, date_pattern='dd/mm/yyyy')
        self.entry_data_inicio.grid(row=0, column=1, padx=10, pady=10)

        self.entry_data_fim = DateEntry(self.filtros_toplevel, date_pattern='dd/mm/yyyy')
        self.entry_data_fim.grid(row=0, column=2, padx=10, pady=10)

        ttk.Label(self.filtros_toplevel, text="Tipo:").grid(row=1, column=0, padx=10, pady=10)
        self.tipo_filtro_var = tk.StringVar(value="Todos")
        ttk.Radiobutton(self.filtros_toplevel, text="Todos", variable=self.tipo_filtro_var, value="Todos").grid(row=1, column=1, padx=10, pady=10)
        ttk.Radiobutton(self.filtros_toplevel, text="Entrada", variable=self.tipo_filtro_var, value="Entrada").grid(row=1, column=2, padx=10, pady=10)
        ttk.Radiobutton(self.filtros_toplevel, text="Saída", variable=self.tipo_filtro_var, value="Saída").grid(row=1, column=3, padx=10, pady=10)

        ttk.Label(self.filtros_toplevel, text="Conta:").grid(row=2, column=0, padx=10, pady=10)
        self.combo_conta_filtro = ttk.Combobox(self.filtros_toplevel)
        self.combo_conta_filtro.grid(row=2, column=1, padx=10, pady=10)
        self._atualizar_lista_contas_filtro()

        ttk.Button(self.filtros_toplevel, text="Aplicar Filtros", command=self._aplicar_filtros).grid(row=3, column=0, columnspan=4, pady=10)

        self.filtros_toplevel.bind("<Escape>", self._limpar_filtros)

    def _atualizar_lista_contas_filtro(self):
        contas = self.db_manager.buscar_contas()
        self.combo_conta_filtro["values"] = [conta[0] for conta in contas]

    def _aplicar_filtros(self):
        data_inicio = self.entry_data_inicio.get()
        data_fim = self.entry_data_fim.get()
        tipo = self.tipo_filtro_var.get()
        conta = self.combo_conta_filtro.get()

        filtros = {}
        if data_inicio and data_fim:
            filtros["data_inicio"] = data_inicio
            filtros["data_fim"] = data_fim
        if tipo != "Todos":
            filtros["tipo"] = tipo
        if conta:
            filtros["conta"] = conta

        self._atualizar_movimentacoes(filtros)
        self.filtros_toplevel.destroy()

    def _limpar_filtros(self, event=None):
        self.entry_data_inicio.set_date(datetime.now())
        self.entry_data_fim.set_date(datetime.now())
        self.tipo_filtro_var.set("Todos")
        self.combo_conta_filtro.set("")
        self._atualizar_movimentacoes()
        self.filtros_toplevel.destroy()

    def _atualizar_resumo(self):
        movimentacoes = self.db_manager.buscar_movimentacoes()
        resumo = {}
        for mov in movimentacoes:
            conta = mov[3]
            tipo = mov[2]
            valor = mov[4]
            if conta not in resumo:
                resumo[conta] = {"Entrada": 0, "Saída": 0}
            resumo[conta][tipo] += valor

        data = [(conta, resumo[conta]["Entrada"] - resumo[conta]["Saída"]) for conta in resumo]
        self._preencher_treeview(self.tree_resumo, data, [0, 1])
        saldo = self.db_manager.calcular_saldo()
        self.label_saldo_total.config(text=f"Saldo Total: R$ {saldo:.2f}")

    def _build_movimentacao_ui(self):
        frame_buttons = ttk.Frame(self.frame_movimentacao, style="Movimentacao.TFrame")
        frame_buttons.pack(fill="x", padx=10, pady=10)

        ttk.Button(frame_buttons, text="Novo Registro", command=self._abrir_tela_registro).pack(side="left", padx=10)
        ttk.Button(frame_buttons, text="Exportar CSV", command=self._exportar_csv).pack(side="right", padx=10)
        ttk.Button(frame_buttons, text="Filtros", command=self._abrir_filtros).pack(side="right", padx=10)
        ttk.Button(frame_buttons, text="Adicionar Contas", command=self._abrir_tela_contas).pack(side="right", padx=10)
        ttk.Button(frame_buttons, text="Editar Registro", command=self._abrir_tela_editar_registro).pack(side="left", padx=10)
        ttk.Button(frame_buttons, text="Excluir Registro", command=self._excluir_movimentacao).pack(side="left", padx=10)

        self.tree_movimentacoes = ttk.Treeview(self.frame_movimentacao, columns=("ID", "Data", "Tipo", "Conta", "Valor", "Observações"), show="headings")
        for col in self.tree_movimentacoes["columns"]:
            self.tree_movimentacoes.heading(col, text=col)
            self.tree_movimentacoes.column(col, width=100)
        self.tree_movimentacoes.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree_movimentacoes.bind("<Double-1>", self._on_tree_select)
        self.frame_movimentacao.bind("<Escape>", self._limpar_filtros_movimentacao)

        self._atualizar_movimentacoes()

    def _limpar_filtros_movimentacao(self, event=None):
        self._atualizar_movimentacoes()

    def _abrir_tela_registro(self):
        self.toplevel = tk.Toplevel(self.root)
        self.toplevel.title("Novo Registro")
        self.toplevel.geometry("400x300")
        self.toplevel.transient(self.root)
        self.toplevel.grab_set()

        ttk.Label(self.toplevel, text="Data:").grid(row=0, column=0, padx=10, pady=10)
        self.entry_data = DateEntry(self.toplevel, date_pattern='dd/mm/yyyy')
        self.entry_data.grid(row=0, column=1, padx=10, pady=10)

        self.tipo_var = tk.StringVar()
        ttk.Radiobutton(self.toplevel, text="Entrada", variable=self.tipo_var, value="Entrada").grid(row=1, column=0, padx=10, pady=10)
        ttk.Radiobutton(self.toplevel, text="Saída", variable=self.tipo_var, value="Saída").grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(self.toplevel, text="Conta:").grid(row=2, column=0, padx=10, pady=10)
        self.combo_conta = ttk.Combobox(self.toplevel)
        self.combo_conta.grid(row=2, column=1, padx=10, pady=10)
        self._atualizar_lista_contas_registro()

        ttk.Label(self.toplevel, text="Valor (R$):").grid(row=3, column=0, padx=10, pady=10)
        self.entry_valor = ttk.Entry(self.toplevel)
        self.entry_valor.grid(row=3, column=1, padx=10, pady=10)

        ttk.Label(self.toplevel, text="Observações:").grid(row=4, column=0, padx=10, pady=10)
        self.entry_observacoes = ttk.Entry(self.toplevel)
        self.entry_observacoes.grid(row=4, column=1, padx=10, pady=10)

        frame_buttons = ttk.Frame(self.toplevel)
        frame_buttons.grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(frame_buttons, text="Salvar", command=self._salvar_registro).pack(side="left", padx=10)
        ttk.Button(frame_buttons, text="Cancelar", command=self.toplevel.destroy).pack(side="right", padx=10)

    def _atualizar_lista_contas_registro(self):
        contas = self.db_manager.buscar_contas()
        self.combo_conta["values"] = [conta[0] for conta in contas]

    def _abrir_tela_contas(self):
        self.contas_toplevel = tk.Toplevel(self.root)
        self.contas_toplevel.title("Gerenciar Contas")
        self.contas_toplevel.geometry("300x400")
        self.contas_toplevel.transient(self.root)
        self.contas_toplevel.grab_set()

        self.tree_contas = ttk.Treeview(self.contas_toplevel, columns=("Conta"), show="headings")
        self.tree_contas.heading("Conta", text="Conta")
        self.tree_contas.column("Conta", width=250)
        self.tree_contas.pack(fill="both", expand=True, padx=10, pady=10)

        frame_entry = ttk.Frame(self.contas_toplevel)
        frame_entry.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame_entry, text="Nome da Conta:").pack(side="left", padx=10)
        self.entry_nome_conta = ttk.Entry(frame_entry)
        self.entry_nome_conta.pack(side="left", padx=10, fill="x", expand=True)

        frame_buttons = ttk.Frame(self.contas_toplevel)
        frame_buttons.pack(fill="x", padx=10, pady=10)

        ttk.Button(frame_buttons, text="Salvar", command=self._adicionar_conta).pack(side="left", padx=10)
        ttk.Button(frame_buttons, text="Excluir", command=self._excluir_conta).pack(side="right", padx=10)

        self._atualizar_lista_contas()

    def _adicionar_conta(self):
        nome_conta = self.entry_nome_conta.get()
        if nome_conta:
            self.db_manager.adicionar_conta(nome_conta)
            self._atualizar_lista_contas()
            self.entry_nome_conta.delete(0, tk.END)

    def _excluir_conta(self):
        selected_item = self.tree_contas.selection()
        if not selected_item:
            messagebox.showerror("Erro", "Nenhuma conta selecionada.")
            return

        item = self.tree_contas.item(selected_item)
        nome_conta = item["values"][0]
        self.db_manager.excluir_conta(nome_conta)
        self._atualizar_lista_contas()

    def _atualizar_lista_contas(self):
        contas = self.db_manager.buscar_contas()
        self._preencher_treeview(self.tree_contas, contas, [0])
        self.combo_conta["values"] = [conta[0] for conta in contas]

    def _salvar_registro(self):
        try:
            data = self.entry_data.get()
            datetime.strptime(data, "%d/%m/%Y")
            tipo = self.tipo_var.get()
            conta = self.combo_conta.get()
            valor = float(self.entry_valor.get())
            observacoes = self.entry_observacoes.get()
            self._validar_campos(data=data, tipo=tipo, conta=conta, valor=valor)
            self.db_manager.adicionar_movimentacao(data=data, tipo=tipo, conta=conta, valor=valor, observacoes=observacoes)
            self._atualizar_resumo()
            self._atualizar_movimentacoes()
            self.toplevel.destroy()
        except ValueError as e:
            messagebox.showerror("Erro de Valor", f"Entrada inválida: {e}")
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro: {e}")

    def _abrir_tela_editar_registro(self):
        selected_item = self.tree_movimentacoes.selection()
        if not selected_item:
            messagebox.showerror("Erro", "Nenhuma movimentação selecionada.")
            return

        item = self.tree_movimentacoes.item(selected_item)
        mov = item["values"]

        self.toplevel = tk.Toplevel(self.root)
        self.toplevel.title("Editar Registro")
        self.toplevel.geometry("400x300")
        self.toplevel.transient(self.root)
        self.toplevel.grab_set()

        ttk.Label(self.toplevel, text="Data:").grid(row=0, column=0, padx=10, pady=10)
        self.entry_data = DateEntry(self.toplevel, date_pattern='dd/mm/yyyy')
        self.entry_data.grid(row=0, column=1, padx=10, pady=10)
        self.entry_data.set_date(datetime.strptime(mov[1], "%d/%m/%Y"))

        self.tipo_var = tk.StringVar(value=mov[2])
        ttk.Radiobutton(self.toplevel, text="Entrada", variable=self.tipo_var, value="Entrada").grid(row=1, column=0, padx=10, pady=10)
        ttk.Radiobutton(self.toplevel, text="Saída", variable=self.tipo_var, value="Saída").grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(self.toplevel, text="Conta:").grid(row=2, column=0, padx=10, pady=10)
        self.combo_conta = ttk.Combobox(self.toplevel)
        self.combo_conta.grid(row=2, column=1, padx=10, pady=10)
        self._atualizar_lista_contas_registro()
        self.combo_conta.set(mov[3])

        ttk.Label(self.toplevel, text="Valor (R$):").grid(row=3, column=0, padx=10, pady=10)
        self.entry_valor = ttk.Entry(self.toplevel)
        self.entry_valor.grid(row=3, column=1, padx=10, pady=10)
        self.entry_valor.insert(0, mov[4])

        ttk.Label(self.toplevel, text="Observações:").grid(row=4, column=0, padx=10, pady=10)
        self.entry_observacoes = ttk.Entry(self.toplevel)
        self.entry_observacoes.grid(row=4, column=1, padx=10, pady=10)
        self.entry_observacoes.insert(0, mov[5])

        frame_buttons = ttk.Frame(self.toplevel)
        frame_buttons.grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(frame_buttons, text="Salvar", command=lambda: self._salvar_edicao(mov[0])).pack(side="left", padx=10)
        ttk.Button(frame_buttons, text="Cancelar", command=self.toplevel.destroy).pack(side="right", padx=10)

    def _salvar_edicao(self, mov_id):
        try:
            data = self.entry_data.get()
            datetime.strptime(data, "%d/%m/%Y")
            tipo = self.tipo_var.get()
            conta = self.combo_conta.get()
            valor = float(self.entry_valor.get())
            observacoes = self.entry_observacoes.get()
            self._validar_campos(data=data, tipo=tipo, conta=conta, valor=valor)
            self.db_manager.editar_movimentacao(mov_id, data=data, tipo=tipo, conta=conta, valor=valor, observacoes=observacoes)
            self._atualizar_resumo()
            self._atualizar_movimentacoes()
            self.toplevel.destroy()
        except ValueError as e:
            messagebox.showerror("Erro de Valor", f"Entrada inválida: {e}")
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro: {e}")

    def _editar_movimentacao(self):
        try:
            selected_item = self.tree_movimentacoes.selection()
            if not selected_item:
                messagebox.showerror("Erro", "Nenhuma movimentação selecionada.")
                return

            item = self.tree_movimentacoes.item(selected_item)
            mov_id = item["values"][0]

            # Coletar dados diretamente dos widgets existentes
            data = self.entry_data.get()
            tipo = self.tipo_var.get()
            conta = self.combo_conta.get()
            valor = float(self.entry_valor.get())
            observacoes = self.entry_observacoes.get()

            # Validar campos
            self._validar_campos(data=data, tipo=tipo, conta=conta, valor=valor)
            
            # Atualizar movimentação
            self.db_manager.editar_movimentacao(mov_id, 
                data=data, tipo=tipo, conta=conta, 
                valor=valor, observacoes=observacoes)
            
            self._atualizar_resumo()
            self._atualizar_movimentacoes()
            self.toplevel.destroy()
        except ValueError as e:
            messagebox.showerror("Erro de Valor", f"Entrada inválida: {e}")
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro: {e}")

    def _excluir_movimentacao(self):
        try:
            selected_item = self.tree_movimentacoes.selection()
            if not selected_item:
                messagebox.showerror("Erro", "Nenhuma movimentação selecionada.")
                return

            item = self.tree_movimentacoes.item(selected_item)
            mov_id = item["values"][0]

            confirm = messagebox.askyesno("Confirmação", "Tem certeza que deseja excluir esta movimentação?")
            if confirm:
                self.db_manager.excluir_movimentacao(mov_id)
                self._atualizar_resumo()
                self._atualizar_movimentacoes()
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro: {e}")

    def _on_tree_select(self, event):
        selected_item = self.tree_movimentacoes.selection()
        if not selected_item:
            return

        item = self.tree_movimentacoes.item(selected_item)
        mov = item["values"]

        self.entry_data.delete(0, tk.END)
        self.entry_data.insert(0, mov[1])
        self.tipo_var.set(mov[2])
        self.combo_conta.set(mov[3])
        self.entry_valor.delete(0, tk.END)
        self.entry_valor.insert(0, mov[4])
        self.entry_observacoes.delete(0, tk.END)
        self.entry_observacoes.insert(0, mov[5])

    def _atualizar_movimentacoes(self, filtros=None):
        query = 'SELECT * FROM movimentacoes'
        params = []

        if filtros:
            conditions = []
            if "data_inicio" in filtros and "data_fim" in filtros:
                conditions.append("data BETWEEN ? AND ?")
                params.extend([filtros["data_inicio"], filtros["data_fim"]])
            if "tipo" in filtros:
                conditions.append("tipo = ?")
                params.append(filtros["tipo"])
            if "conta" in filtros:
                conditions.append("conta = ?")
                params.append(filtros["conta"])

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        movimentacoes = self.db_manager.fetch_all(query, params)
        self._preencher_treeview(self.tree_movimentacoes, movimentacoes, [0, 1, 2, 3, 4, 5])

    def _preencher_treeview(self, treeview, data, columns):
        for item in treeview.get_children():
            treeview.delete(item)
        for row in data:
            treeview.insert("", "end", values=[row[col] for col in columns])

    def _limpar_campos(self):
        for widget in self.widgets.values():
            widget.delete(0, tk.END)

    def _limpar_campos_registro(self):
        self.entry_data.delete(0, tk.END)
        self.tipo_var.set('')
        self.combo_conta.set('')
        self.entry_valor.delete(0, tk.END)
        self.entry_observacoes.delete(0, tk.END)

    def _exportar_csv(self):
        self.db_manager.exportar_csv()

    def _validar_campos(self, **kwargs):
        if kwargs["tipo"] not in ["Entrada", "Saída"]:
            raise ValueError("O tipo deve ser 'Entrada' ou 'Saída'.")
        if not kwargs["conta"]:
            raise ValueError("A conta não pode estar vazia.")
        if kwargs["valor"] <= 0:
            raise ValueError("O valor deve ser maior que zero.")

if __name__ == "__main__":
    root = tk.Tk()
    app = UIManager(root)
    root.mainloop()
