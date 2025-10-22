import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

DB_PATH = "teste.db"

# --------------------- Database helpers ---------------------

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Cria a tabela se não existir
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
    # Verifica e adiciona colunas ausentes (corrige bancos antigos)
    existing_cols = [row["name"] for row in c.execute("PRAGMA table_info(atos)").fetchall()]
    if "data_ocorrido" not in existing_cols:
        c.execute("ALTER TABLE atos ADD COLUMN data_ocorrido TEXT")
    conn.commit()
    conn.close()


def add_ato(nome_ato: str, valor: float, data_ocorrido: str, descricao: str = ""):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO atos (nome_ato, valor, data_ocorrido, descricao, criado_em) VALUES (?, ?, ?, ?, ?)",
        (nome_ato, valor, data_ocorrido, descricao, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


def get_atos(start_date=None, end_date=None, search=None):
    conn = get_connection()
    c = conn.cursor()
    query = "SELECT * FROM atos"
    conditions = []
    params = []
    if start_date:
        conditions.append("date(data_ocorrido) >= date(?)")
        params.append(start_date)
    if end_date:
        conditions.append("date(data_ocorrido) <= date(?)")
        params.append(end_date)
    if search:
        conditions.append("nome_ato LIKE ?")
        params.append(f"%{search}%")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY date(data_ocorrido) DESC, id DESC"
    rows = c.execute(query, params).fetchall()
    conn.close()

    df = pd.DataFrame(rows)
    if not df.empty:
        if "data_ocorrido" in df.columns:
            df['data_ocorrido'] = pd.to_datetime(df['data_ocorrido'], errors='coerce').dt.date
        if "criado_em" in df.columns:
            df['criado_em'] = pd.to_datetime(df['criado_em'], errors='coerce')
    return df


def delete_ato(ato_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM atos WHERE id = ?", (ato_id,))
    conn.commit()
    conn.close()


# --------------------- Export helpers ---------------------

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="atos")
    return output.getvalue()


# --------------------- UI helpers ---------------------

def format_currency(v):
    try:
        return f"R$ {v:,.2f}"
    except Exception:
        return v


# --------------------- App ---------------------

st.set_page_config(page_title="Controle de Atos - Cartório", layout="wide")
init_db()

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📁 Controle de Atos - Cartório")
    st.markdown("Aplicação para **registrar, filtrar e exportar** atos realizados no cartório.")
with col2:
    st.image("https://upload.wikimedia.org/wikipedia/commons/7/78/Document-icon.svg", width=80)

st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("Filtros")
    start_date = st.date_input("Data inicial", value=None)
    end_date = st.date_input("Data final", value=None)
    search = st.text_input("Pesquisar por nome do ato")
    if st.button("Aplicar filtros"):
        st.session_state["filters"] = {
            "start_date": start_date,
            "end_date": end_date,
            "search": search
        }
    st.markdown("---")
    st.header("Exportação")
    st.write("Exporte os registros filtrados em CSV ou Excel.")

# Main layout
left, right = st.columns([2, 1])

# --------------------- Formulário ---------------------
with left:
    st.subheader("📝 Novo registro")
    with st.form("form_add"):
        nome_ato = st.text_input("Nome do ato", max_chars=200)
        valor = st.number_input("Valor do ato (R$)", min_value=0.00, step=0.01, format="%.2f")
        data_ocorrido = st.date_input("Data do ocorrido")
        descricao = st.text_area("Descrição (opcional)", height=80)
        submitted = st.form_submit_button("Salvar registro")

    if submitted:
        if not nome_ato.strip():
            st.warning("O campo **Nome do ato** é obrigatório.")
        else:
            add_ato(nome_ato.strip(), float(valor), data_ocorrido.isoformat(), descricao.strip())
            st.success("✅ Registro salvo com sucesso!")
            st.rerun()

    st.markdown("---")
    st.subheader("📋 Registros")

    filters = st.session_state.get("filters", {})
    df = get_atos(
        start_date=filters.get("start_date"),
        end_date=filters.get("end_date"),
        search=filters.get("search")
    )

    if df.empty:
        st.info("Nenhum registro encontrado com os filtros selecionados.")
    else:
        total_valor = df["valor"].sum()
        count = len(df)
        st.metric("Total de registros", count)
        st.metric("Valor total (R$)", format_currency(total_valor))

        view_df = df.copy()
        view_df["valor"] = view_df["valor"].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(view_df[["id", "nome_ato", "valor", "data_ocorrido", "descricao", "criado_em"]])

        st.write("")
        cols = st.columns([3, 1])
        with cols[0]:
            selected_id = st.number_input("ID do registro para deletar", min_value=0, value=0, step=1)
        with cols[1]:
            if st.button("🗑️ Deletar registro"):
                if selected_id == 0:
                    st.warning("Informe um **ID válido**.")
                elif selected_id in df["id"].values:
                    delete_ato(int(selected_id))
                    st.success(f"Registro {selected_id} deletado.")
                    st.rerun()
                else:
                    st.error("ID não encontrado nos registros atuais.")

        csv = df.to_csv(index=False).encode("utf-8")
        excel_bytes = to_excel_bytes(df)
        st.download_button("⬇️ Baixar CSV", data=csv, file_name="atos_cartorio.csv", mime="text/csv")
        st.download_button("⬇️ Baixar XLSX", data=excel_bytes,
                           file_name="atos_cartorio.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --------------------- Visão rápida ---------------------
with right:
    st.subheader("📊 Visão rápida")
    summary = get_atos()
    if not summary.empty:
        df_month = summary.copy()
        df_month["mes"] = pd.to_datetime(df_month["data_ocorrido"], errors="coerce").dt.to_period("M")
        pivot = df_month.groupby("mes")["valor"].agg(["count", "sum"]).reset_index()
        pivot["mes"] = pivot["mes"].astype(str)
        st.table(pivot.sort_values("mes", ascending=False).head(6))
    else:
        st.info("Sem registros para mostrar na visão rápida.")

st.markdown("---")
st.caption("💼 Desenvolvido para uso em cartórios — versão segura e persistente.")
