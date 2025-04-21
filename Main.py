import streamlit as st
import pandas as pd
import datetime
import asyncio
import aiohttp
import requests as r
from bs4 import BeautifulSoup, SoupStrainer

# ----------------------------------------
# 🔧 Configuración
# ----------------------------------------
FIFA_URL = 'https://www.fifa.com/fifa-world-ranking/ranking-table/men/rank'
FIRST_DATE = 'id1'

# ----------------------------------------
# 🏁 Utilidad para mostrar banderas
# ----------------------------------------
def get_flag_emoji(country):
    flags = {
        'Argentina': '🇦🇷', 'France': '🇫🇷', 'Brazil': '🇧🇷', 'Germany': '🇩🇪', 'Italy': '🇮🇹',
        'Spain': '🇪🇸', 'Portugal': '🇵🇹', 'Netherlands': '🇳🇱', 'Uruguay': '🇺🇾', 'Belgium': '🇧🇪',
        'Croatia': '🇭🇷', 'England': '🇬🇧', 'USA': '🇺🇸', 'Mexico': '🇲🇽', 'Japan': '🇯🇵',
    }
    return flags.get(country, '🏳️')

# ----------------------------------------
# 🌐 Scraping de fechas disponibles
# ----------------------------------------
def get_dates_html():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    page_source = r.get(f'{FIFA_URL}/{FIRST_DATE}/', headers=headers)
    page_source.raise_for_status()
    dates = BeautifulSoup(page_source.text, 'html.parser',
                          parse_only=SoupStrainer('li', attrs={'class': 'fi-ranking-schedule__nav__item'}))
    return dates

def create_dates_dataset(html_dates):
    date_ids = [li['data-value'] for li in html_dates]
    dates = [li.text.strip() for li in html_dates]
    df = pd.DataFrame({'date': pd.to_datetime(dates, format='%d %B %Y'), 'date_id': date_ids})
    df.sort_values('date', inplace=True)
    return df

# ----------------------------------------
# 🔍 Scraping de ranking FIFA por fecha
# ----------------------------------------
async def get_rank_page(date_id, session):
    headers = {"User-Agent": "Mozilla/5.0"}
    async with session.get(f'{FIFA_URL}/{date_id}/', headers=headers) as response:
        if response.status == 200:
            return {'page': await response.text(), 'id': date_id}
        else:
            return None

def scrapy_rank_table(page, date):
    rows = BeautifulSoup(page, 'html.parser', parse_only=SoupStrainer('tbody')).find_all('tr')
    tabla = []
    for row in rows:
        try:
            tabla.append({
                'id': int(row['data-team-id']),
                'country': row.find('span', {'class': 'fi-t__nText'}).text.strip(),
                'rank': int(row.find('td', {'class': 'fi-table__rank'}).text),
                'points': int(row.find('td', {'class': 'fi-table__points'}).text),
                'confederation': row.find('td', {'class': 'fi-table__confederation'}).text.strip(),
                'rank_date': date
            })
        except Exception as e:
            print(f"❌ Error al procesar fila: {e}")
            continue
    return tabla


async def parse_ranks(df_dates):
    final_df = pd.DataFrame()
    async with aiohttp.ClientSession() as session:
        tasks = [get_rank_page(row.date_id, session) for _, row in df_dates.iterrows()]
        results = await asyncio.gather(*tasks)
        for result in results:
            if result:
                date = df_dates[df_dates.date_id == result['id']].date.iloc[0]
                tabla = scrapy_rank_table(result['page'], date)
                final_df = pd.concat([final_df, pd.DataFrame(tabla)], ignore_index=True)
    return final_df

# ----------------------------------------
# 🖥️ Interfaz Streamlit
# ----------------------------------------
st.set_page_config(page_title="🏆 Ranking FIFA", layout="centered")
st.title("🌍 Ranking FIFA Masculino (última fecha disponible)")

if 'ranking_df' not in st.session_state:
    with st.spinner("Obteniendo datos desde FIFA.com..."):
        html_dates = get_dates_html()
        fechas_df = create_dates_dataset(html_dates)
        latest_date_df = fechas_df.tail(1)  # solo la más reciente
        ranking_df = asyncio.run(parse_ranks(latest_date_df))

        # Agregar banderas
        ranking_df['Equipo'] = ranking_df['country'].apply(lambda x: f"{get_flag_emoji(x)} {x}")
        st.session_state['ranking_df'] = ranking_df

# Menú lateral
menu = st.sidebar.radio("Menú", ["Ranking FIFA", "Detalle por Selección"])
ranking_df = st.session_state['ranking_df']

# Menú principal
if menu == "Ranking FIFA":
    st.subheader("📊 Tabla de posiciones")
    st.dataframe(ranking_df[['rank_date', 'rank', 'Equipo', 'points', 'confederation']])
elif menu == "Detalle por Selección":
    seleccion = st.selectbox("🌐 Selección", ranking_df['Equipo'].tolist())
    fila = ranking_df[ranking_df['Equipo'] == seleccion]
    if not fila.empty:
        fila = fila.iloc[0]
        st.markdown(f"## {seleccion}")
        st.metric("Posición FIFA", fila['rank'])
        st.metric("Puntos", fila['points'])
        st.write(f"🌍 Confederación: {fila['confederation']}")
    else:
        st.warning("No se encontró la selección.")
