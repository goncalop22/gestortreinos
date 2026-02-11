import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Analítico ATEC", layout="wide")

# --- FUNÇÕES DE BASE DE DADOS ---
def init_db():
    """Cria tabelas de exemplo e dados fictícios para a disciplina"""
    conn = sqlite3.connect('atec_vendas.db')
    cursor = conn.cursor()
    
    # Criar Tabelas (Exemplo de DDL)
    cursor.execute('''CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY, nome TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY, nome TEXT, id_categoria INTEGER, preco REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY, id_produto INTEGER, data DATE, quantidade INTEGER)''')
    
    # Inserir dados apenas se estiverem vazias (Exemplo de DML)
    cursor.execute("SELECT count(*) FROM categorias")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO categorias VALUES (1, 'Hardware'), (2, 'Software'), (3, 'Serviços')")
        cursor.execute("INSERT INTO produtos VALUES (1, 'Teclado RGB', 1, 45.0), (2, 'Rato Pro', 1, 30.0), (3, 'Windows 11 Pro', 2, 150.0), (4, 'Suporte Técnico', 3, 80.0)")
        cursor.execute("INSERT INTO vendas VALUES (1,1,'2024-01-10', 5), (2,2,'2024-01-12', 10), (3,3,'2024-01-15', 2), (4,1,'2024-02-01', 3), (5,4,'2024-02-05', 1)")
    
    conn.commit()
    conn.close()

def run_query(query, params=()):
    with sqlite3.connect('atec_vendas.db') as conn:
        return pd.read_sql_query(query, conn, params=params)

# Inicializar DB
init_db()

# --- INTERFACE ---
st.title("🚀 Dashboard de Análise de Dados (SQL Completo)")
st.markdown("Este dashboard executa consultas complexas integrando **Python e SQL**.")

# --- SIDEBAR (FILTROS) ---
st.sidebar.header("Filtros de Pesquisa")
data_inicio = st.sidebar.date_input("Data de Início", value=pd.to_datetime("2024-01-01"))
data_fim = st.sidebar.date_input("Data de Fim", value=pd.to_datetime("2024-12-31"))

# --- CONSULTAS COMPLEXAS ---

# 1. KPI - Métricas Totais (SELECT com Agregação e Join)
query_kpi = """
    SELECT 
        SUM(v.quantidade * p.preco) as fatura_total,
        AVG(v.quantidade * p.preco) as ticket_medio,
        COUNT(v.id) as total_vendas
    FROM vendas v
    JOIN produtos p ON v.id_produto = p.id
    WHERE v.data BETWEEN ? AND ?
"""
df_kpi = run_query(query_kpi, (data_inicio, data_fim))

# Exibir Métricas
col1, col2, col3 = st.columns(3)
col1.metric("Faturação Total", f"{df_kpi['fatura_total'][0]:.2f} €")
col2.metric("Ticket Médio", f"{df_kpi['ticket_medio'][0]:.2f} €")
col3.metric("Nº de Vendas", int(df_kpi['total_vendas'][0]))

st.divider()

# 2. Gráfico: Vendas por Categoria (JOIN + GROUP BY)
st.subheader("📦 Performance por Categoria")
query_cat = """
    SELECT c.nome as categoria, SUM(v.quantidade * p.preco) as total
    FROM vendas v
    INNER JOIN produtos p ON v.id_produto = p.id
    INNER JOIN categorias c ON p.id_categoria = c.id
    WHERE v.data BETWEEN ? AND ?
    GROUP BY c.nome
    ORDER BY total DESC
"""
df_cat = run_query(query_cat, (data_inicio, data_fim))
fig_pizza = px.pie(df_cat, values='total', names='categoria', hole=0.3)
st.plotly_chart(fig_pizza, use_container_width=True)

# 3. Gráfico: Ranking de Produtos (Top 5)
st.subheader("🏆 Top Produtos Mais Vendidos")
query_top = """
    SELECT p.nome, SUM(v.quantidade) as qtd_total
    FROM vendas v
    JOIN produtos p ON v.id_produto = p.id
    GROUP BY p.nome
    ORDER BY qtd_total DESC
    LIMIT 5
"""
df_top = run_query(query_top)
fig_bar = px.bar(df_top, x='nome', y='qtd_total', color='qtd_total', labels={'nome': 'Produto', 'qtd_total': 'Quantidade'})
st.plotly_chart(fig_bar, use_container_width=True)

# 4. Visualização da Tabela Bruta (SELECT *)
with st.expander("🔍 Ver Dados Brutos (Joins Detalhados)"):
    query_raw = """
        SELECT v.id, v.data, p.nome as produto, c.nome as categoria, v.quantidade, p.preco, (v.quantidade * p.preco) as subtotal
        FROM vendas v
        LEFT JOIN produtos p ON v.id_produto = p.id
        LEFT JOIN categorias c ON p.id_categoria = c.id
        ORDER BY v.data DESC
    """
    st.dataframe(run_query(query_raw), use_container_width=True)
