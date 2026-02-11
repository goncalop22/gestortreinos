import streamlit as st
import pandas as pd
import mysql.connector
import requests
from bs4 import BeautifulSoup

# --- CONFIGURAÇÃO DA BASE DE DADOS ---
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # ALTERA AQUI SE TIVERES PASSWORD
    'database': 'gestao_desportiva'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# --- FUNÇÃO DE SCRAPING (ADAPTÁVEL) ---
def extrair_dados_liga(url):
    """
    Tenta extrair dados do site. 
    NOTA: Os seletores 'td' e 'class' variam conforme o site da Federação.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # EXEMPLO: Procura a primeira equipa e golos numa tabela
        # Se o site for da FPF ou similar, estas tags têm de ser ajustadas
        equipa = soup.find('td', class_='nome-equipa').text.strip() if soup.find('td', class_='nome-equipa') else "Equipa Desconhecida"
        g_pro = float(soup.find('td', class_='golos-pro').text) if soup.find('td', class_='golos-pro') else 0.0
        g_con = float(soup.find('td', class_='golos-contra').text) if soup.find('td', class_='golos-contra') else 0.0
        
        return {'equipa': equipa, 'g_pro': g_pro, 'g_con': g_con}
    except Exception as e:
        st.error(f"Erro no Scraper: {e}. Verifique se o URL é válido ou se os seletores HTML mudaram.")
        return None

# --- FUNÇÃO PARA CHAMAR A PROCEDURE DO HEIDISQL ---
def obter_sugestao_treino(id_equipa):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"CALL sp_SugerirTreino({id_equipa})")
        resultado = cursor.fetchone()
        conn.close()
        return resultado
    except Exception as e:
        st.error(f"Erro ao chamar Procedure: {e}")
        return None

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Coach Scout Pro", layout="wide")

st.title("🛡️ Sistema de Automação Tática")
st.markdown("---")

# Sidebar para Navegação
menu = ["📊 Dashboard & Decisão", "🌐 Scraper da Liga", "📝 Dados Manuais"]
choice = st.sidebar.selectbox("Menu Principal", menu)

if choice == "📊 Dashboard & Decisão":
    st.header("Análise Tática via Base de Dados")
    
    # Selecionar adversário da BD
    conn = get_db_connection()
    lista_adv = pd.read_sql("SELECT DISTINCT id_equipa, nome_equipa FROM scouting_adversarios", conn)
    conn.close()
    
    if not lista_adv.empty:
        escolha_adv = st.selectbox("Selecione o Adversário para analisar:", 
                                   lista_adv['id_equipa'], 
                                   format_func=lambda x: lista_adv[lista_adv['id_equipa']==x]['nome_equipa'].values[0])
        
        if st.button("Gerar Plano de Treino"):
            analise = obter_sugestao_treino(escolha_adv)
            if analise:
                st.success(f"### {analise['Sugestao']}")
                st.info(f"**Justificação:** {analise['Razao']}")
    else:
        st.warning("A base de dados está vazia. Use o Scraper primeiro!")

elif choice == "🌐 Scraper da Liga":
    st.header("Recolha Automática de Resultados")
    url_liga = st.text_input("Cole aqui o URL da página de classificação/resultados:")
    id_manual = st.number_input("Atribua um ID numérico a esta equipa:", min_value=1, value=1)
    
    if st.button("Executar Scraping"):
        with st.spinner("A ler dados da federação..."):
            dados = extrair_dados_liga(url_liga)
            if dados:
                conn = get_db_connection()
                cursor = conn.cursor()
                query = """INSERT INTO scouting_adversarios (id_equipa, nome_equipa, golos_pro, golos_contra) 
                           VALUES (%s, %s, %s, %s)"""
                cursor.execute(query, (id_manual, dados['equipa'], dados['g_pro'], dados['g_con']))
                conn.commit()
                conn.close()
                st.balloons()
                st.success(f"Dados da equipa '{dados['equipa']}' guardados no MySQL!")

elif choice == "📝 Dados Manuais":
    st.header("Inserção Manual de Scout")
    with st.form("form_manual"):
        id_e = st.number_input("ID da Equipa", min_value=1)
        nome_e = st.text_input("Nome da Equipa")
        gp = st.number_input("Média Golos Marcados", step=0.1)
        gs = st.number_input("Média Golos Sofridos", step=0.1)
        
        if st.form_submit_button("Guardar na BD"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO scouting_adversarios (id_equipa, nome_equipa, golos_pro, golos_contra) VALUES (%s, %s, %s, %s)", 
                           (id_e, nome_e, gp, gs))
            conn.commit()
            conn.close()
            st.success("Dados inseridos com sucesso!")

# Tabela de visualização rápida no fundo
st.markdown("---")
st.subheader("Histórico de Scouting (BD MySQL)")
conn = get_db_connection()
df_total = pd.read_sql("SELECT * FROM scouting_adversarios ORDER BY data_analise DESC", conn)
conn.close()
st.dataframe(df_total, use_container_width=True)
