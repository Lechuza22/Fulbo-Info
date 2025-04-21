import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import emoji

# -------------------------------------
# 🏴 Utilidad para convertir país a emoji de bandera
# -------------------------------------
def get_flag_emoji(country_name):
    codes = {
        'Argentina': 'AR', 'France': 'FR', 'Brazil': 'BR', 'England': 'GB', 'Belgium': 'BE',
        'Croatia': 'HR', 'Netherlands': 'NL', 'Italy': 'IT', 'Spain': 'ES', 'Portugal': 'PT',
        'Germany': 'DE', 'Uruguay': 'UY', 'Morocco': 'MA', 'Mexico': 'MX', 'USA': 'US',
        'Colombia': 'CO', 'Switzerland': 'CH', 'Japan': 'JP', 'Senegal': 'SN', 'Korea Republic': 'KR',
    }
    code = codes.get(country_name, None)
    if code:
        return chr(127397 + ord(code[0])) + chr(127397 + ord(code[1]))
    else:
        return "🏳️"

# -------------------------------------
# 🌐 Scraping ranking FIFA
# -------------------------------------
@st.cache_data
def obtener_ranking_fifa():
    url = 'https://www.fifaindex.com/ranking/'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        tabla = soup.find('table', {'class': 'table table-striped'})
        filas = tabla.find('tbody').find_all('tr')

        ranking = []
        for fila in filas:
            columnas = fila.find_all('td')
            puesto = columnas[0].text.strip()
            pais = columnas[1].text.strip()
            puntos = columnas[2].text.strip()

            ranking.append({
                'Posición': int(puesto),
                'País': f"{get_flag_emoji(pais)} {pais}",
                'Puntos': float(puntos.replace(",", ""))
            })

        df = pd.DataFrame(ranking)
        return df
    else:
        st.error("❌ No se pudo obtener el ranking FIFA.")
        return pd.DataFrame()

# -------------------------------------
# 📊 Mostrar datos por selección
# -------------------------------------
def mostrar_info_seleccion(df):
    st.subheader("🌍 Selección Nacional")
    paises = df['País'].tolist()
    seleccion = st.selectbox("Seleccioná una selección:", paises)
    
    fila = df[df['País'] == seleccion].iloc[0]
    st.markdown(f"### {seleccion}")
    st.metric(label="📈 Posición", value=fila['Posición'])
    st.metric(label="💯 Puntos FIFA", value=fila['Puntos'])

# -------------------------------------
# 🎯 Interfaz principal
# -------------------------------------
st.set_page_config(page_title="🏆 Ranking FIFA", layout="centered")

st.sidebar.title("⚽ Menú principal")
menu = st.sidebar.radio("Ir a:", ["Ranking FIFA", "Selecciones"])

# Cargar ranking
ranking_df = obtener_ranking_fifa()

if menu == "Ranking FIFA":
    st.title("🏆 Ranking FIFA actualizado")
    st.dataframe(ranking_df, use_container_width=True)
elif menu == "Selecciones":
    mostrar_info_seleccion(ranking_df)

