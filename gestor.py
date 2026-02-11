import streamlit as st
import pandas as pd
import mysql.connector

# Configuração de ligação (ajusta as tuas credenciais)
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="gestao_desportiva"
    )

def chamar_procedure_treino(id_equipa):
    """Chama a Stored Procedure criada no HeidiSQL"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # Retorna como dicionário para facilitar
    
    # Executa o comando CALL
    cursor.execute(f"CALL sp_SugerirTreino({id_equipa})")
    
    # Recupera o resultado da Procedure
    resultado = cursor.fetchone()
    
    conn.close()
    return resultado

# --- INTERFACE STREAMLIT ---
st.title("⚽ Coach Assistant - Versão Stored Procedure")

# Exemplo de ID do adversário (em produção, isto viria do scraper ou de um select)
id_do_rival = st.number_input("ID do Adversário para Análise", value=1)

if st.button("Analisar Próximo Treino"):
    # Chamamos a lógica que está DENTRO do SQL
    analise = chamar_procedure_treino(id_do_rival)
    
    if analise:
        st.subheader("💡 Sugestão da Base de Dados:")
        st.warning(f"**{analise['Sugestao']}**")
        st.info(f"**Motivo:** {analise['Razao']}")
    else:
        st.error("Não há dados de scouting suficientes para este ID de equipa.")

# --- PARTE DO SCRAPER (ADAPTADA) ---
st.markdown("---")
st.header("📥 Inserir Dados de Scouting")
with st.form("scout_form"):
    nome_e = st.text_input("Nome da Equipa")
    g_pro = st.number_input("Golos Marcados (Média)", min_value=0.0)
    g_con = st.number_input("Golos Sofridos (Média)", min_value=0.0)
    
    if st.form_submit_button("Guardar no SQL"):
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "INSERT INTO scouting_adversarios (id_equipa, nome_equipa, golos_pro, golos_contra) VALUES (%s, %s, %s, %s)"
        # Aqui usei o valor 1 como ID de equipa padrão para o teste
        cursor.execute(query, (1, nome_e, g_pro, g_con))
        conn.commit()
        conn.close()
        st.success("Dados inseridos! Agora já podes clicar em 'Analisar'.")
