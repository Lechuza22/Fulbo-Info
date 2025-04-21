import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.express as px
import emoji

# Función para obtener el ranking FIFA
def obtener_ranking_fifa():
    url = "https://inside.fifa.com/es/fifa-world-ranking/men"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Aquí debes analizar la estructura HTML de la página y extraer los datos necesarios.
    # Este es un ejemplo genérico; deberás ajustarlo según la estructura real de la página.
    tabla = soup.find('table')  # Encuentra la tabla del ranking
    filas = tabla.find_all('tr')[1:]  # Omite la cabecera

    datos = []
    for fila in filas:
        columnas = fila.find_all('td')
        if len(columnas) >= 3:
            posicion = columnas[0].text.strip()
            equipo = columnas[1].text.strip()
            puntos = columnas[2].text.strip()
            datos.append({
                'Posición': posicion,
                'Equipo': equipo,
                'Puntos': puntos
            })

    df = pd.DataFrame(datos)
    return df

# Función para mostrar emojis de banderas
def obtener_bandera(pais):
    # Diccionario de ejemplo; deberás completarlo con más países.
    banderas = {
        'Argentina': '🇦🇷',
        'Brasil': '🇧🇷',
        'Francia': '🇫🇷',
        'Alemania': '🇩🇪',
        'España': '🇪🇸'
    }
    return banderas.get(pais, '')

# Interfaz de Streamlit
st.title("🌍 Ranking FIFA y Estadísticas de Selecciones")

menu = st.sidebar.selectbox("Menú", ["Ranking FIFA", "Selecciones"])

if menu == "Ranking FIFA":
    st.header("📊 Ranking FIFA Masculino")
    df_ranking = obtener_ranking_fifa()
    if not df_ranking.empty:
        # Agrega la bandera al nombre del equipo
        df_ranking['Equipo'] = df_ranking['Equipo'].apply(lambda x: f"{obtener_bandera(x)} {x}")
        st.dataframe(df_ranking)
        # Gráfico de barras
        fig = px.bar(df_ranking.head(10), x='Equipo', y='Puntos', title='Top 10 del Ranking FIFA')
        st.plotly_chart(fig)
    else:
        st.warning("No se pudieron obtener los datos del ranking.")

elif menu == "Selecciones":
    st.header("📈 Estadísticas de Selecciones")
    st.info("Esta sección está en desarrollo. Próximamente podrás ver estadísticas detalladas de cada selección.")
