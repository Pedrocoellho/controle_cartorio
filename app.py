import streamlit as st
import pandas as pd
import os
from datetime import datetime

DATA_FILE = "dados_cartorio.csv"

# Função para carregar dados
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=["id", "nome_ato", "valor", "data_ocorrido", "descricao", "criado_em"])
    return df

# Função para salvar dados
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Função para adicionar novo registro
def add_record(nome_ato, valor, data_ocorrido, descricao):
    df = load_data()
    novo_id = df["id"].max() + 1 if not df.empty else 1
    novo_registro = pd.DataFrame([{
        "id": novo_id,
        "nome_ato": nome_ato,
        "valor": valor,
        "data_ocorrido": data_ocorrido,
        "descricao": descricao,
        "criado_em": datetime.now().strftime("%d/%m/%Y %H:%M")
    }])
    df = pd.concat([df, novo_registro], ignore_index=True)
    save_data(df)
    st.success("✅ Registro salvo com sucesso!")
    st.rerun()

# Função para deletar registro
def delete_record(id_registro):
    df = load_data()
    df = df[df["id"] != id_registro]
    save_data(df)
    st.warning(f"🗑️ Registro {id_registro} excluído com sucesso!")
    st.rerun()

# --- INTERFACE ---
st.set_page_config("Controle Cartório", layout="wide")
st.sidebar.header("Filtros")

data_inicial = st.sidebar.date_input("Data inicial")
data_final = st.sidebar.date_input("Data final")
filtro_nome = st.sidebar.text_input("Pesquisar por nome do ato")
st.sidebar.button("Aplicar filtros")

st.title("📋 Registros")

# --- FORMULÁRIO ---
with st.form("form_ato"):
    nome_ato = st.text_input("Nome do ato")
    valor = st.number_input("Valor do ato (R$)", min_value=0.0, step=0.01)
    data_ocorrido = st.date_input("Data do ocorrido")
    descricao = st.text_area("Descrição (opcional)")
    submit = st.form_submit_button("Salvar registro")

if submit:
    add_record(nome_ato, valor, data_ocorrido.strftime("%d/%m/%Y"), descricao)

# --- TABELA ---
df = load_data()

if not df.empty:
    st.subheader("📊 Registros salvos")
    for i, row in df.iterrows():
        cols = st.columns([0.2, 1, 0.5, 0.6, 1, 0.6, 0.1])
        cols[0].write(row["id"])
        cols[1].write(row["nome_ato"])
        cols[2].write(f"R$ {row['valor']:.2f}")
        cols[3].write(row["data_ocorrido"])
        cols[4].write(row["descricao"] if pd.notna(row["descricao"]) else "-")
        cols[5].write(row["criado_em"])
        if cols[6].button("🗑️", key=f"del_{row['id']}"):
            delete_record(row["id"])
else:
    st.info("Nenhum registro encontrado.")
