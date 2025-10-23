import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Caminho do banco de dados
DB_PATH = "atos_cartorio.db"

# --------------------- FUNÇÕES DE BANCO ---------------------

def init_db():
    """Inicializa o banco de dados se ele não existir."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS atos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_ato TEXT NOT NULL,
            valor REAL NOT NULL,
            data_ocorrido TEXT,
            descricao TEXT,
            criado_em TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def ensure_columns():
    """Garante que todas as colunas necessárias existam na tabela."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("PRAGMA table_info(atos)")
    cols = [row[1] for row in c.fetchall()]

    # Adiciona colunas que estiverem faltando
    if "data_ocorrido" not in cols:
        c.execute("ALTER TABLE atos ADD COLUMN data_ocorrido TEXT")
    if "descricao" not in cols:
        c.execute("ALTER TABLE atos ADD COLUMN descricao TEXT")
    if "criado_em" not in cols:
        c.execute("ALTER TABLE atos ADD COLUMN criado_em TEXT")

    conn.commit()
    conn.close()

def add_ato(nome_ato, valor, data_ocorrido, descricao):
    """Insere um novo registro na tabela."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO atos (nome_ato, valor, data_ocorrido, descricao, criado_em)
        VALUES (?, ?, ?, ?, ?)
    """, (nome_ato, valor, data_ocorrido, descricao, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_atos(start_date=None, end_date=None, search=None):
    """Retorna registros com base em filtros."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM atos", conn)
    conn.close()

    if "data_ocorrido" in df.columns:
        df["data_ocorrido"] = pd.to_datetime(df["data_ocorrido"], errors='coerce')

    if start_date:
        df = df[df["data_ocorrido"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["data_ocorrido"] <= pd.to_datetime(end_date)]
    if search:
        df = df[df["nome_ato"].str.contains(search, case=False, na=False)]

    return df

# --------------------- CONFIGURAÇÃO DO APP ---------------------

st.set_page_config(
    page_title="Controle de Atos de Cartório",
    page_icon="📜",
    layout="wide"
)

st.title("📜 Controle de Atos de Cartório")

# Inicializa e corrige o banco
init_db()
ensure_columns()

# --------------------- SIDEBAR ---------------------

st.sidebar.title("Filtros")

start_date = st.sidebar.date_input("Data inicial", value=None)
end_date = st.sidebar.date_input("Data final", value=None)
search = st.sidebar.text_input("Pesquisar por nome do ato")

st.sidebar.markdown("---")
if st.sidebar.button("Aplicar filtros"):
    st.session_state["filter_applied"] = True
else:
    st.session_state["filter_applied"] = False

st.sidebar.markdown("### Exportação")
st.sidebar.caption("Exporte os registros filtrados em CSV ou Excel.")

# --------------------- FORMULÁRIO ---------------------

st.subheader("Adicionar novo ato")

with st.form("form_ato"):
    nome_ato = st.text_input("Nome do ato")
    valor = st.number_input("Valor do ato (R$)", min_value=0.0, step=0.01)
    data_ocorrido = st.date_input("Data do ocorrido")
    descricao = st.text_area("Descrição (opcional)")
    submit = st.form_submit_button("Salvar registro")

    if submit:
        if nome_ato and valor > 0:
            add_ato(nome_ato, valor, data_ocorrido.strftime("%Y-%m-%d"), descricao)
            st.success("✅ Registro salvo com sucesso!")
        else:
            st.warning("⚠️ Preencha todos os campos obrigatórios.")

# --------------------- TABELA DE REGISTROS ---------------------

st.markdown("---")
st.subheader("📚 Registros")

df = get_atos(
    start_date=start_date if start_date else None,
    end_date=end_date if end_date else None,
    search=search if search else None
)

if not df.empty:
    st.dataframe(df, use_container_width=True)

    # Exportação
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar registros (CSV)", csv, "registros_cartorio.csv", "text/csv")

else:
    st.info("Nenhum registro encontrado com os filtros selecionados.")

# --------------------- RODAPÉ ---------------------

st.markdown("---")
st.caption("🪶 Desenvolvido para uso em cartórios — versão persistente e segura.")
