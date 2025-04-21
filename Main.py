import streamlit as st
import pandas as pd
import asyncio
import aiohttp
import datetime
from bs4 import BeautifulSoup, SoupStrainer
import requests as r
import logging

# ------------------------
# Logging
# ------------------------
logger = logging.getLogger('log')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# ------------------------
# URLs y Constantes
# ------------------------
FIFA_URL = 'https://www.fifa.com/fifa-world-ranking/ranking-table/men/rank'
FIRST_DATE = 'id1'

# ------------------------
# Scraping Fechas
# ------------------------
def get_dates_html():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    page_source = r.get(f'{FIFA_URL}/{FIRST_DATE}/', headers=headers)
    page_source.raise_for_status()
    dates = BeautifulSoup(page_source.text,
                          'html.parser',
                          parse_only=SoupStrainer('li', attrs={'class': 'fi-ranking-schedule__nav__item'}))
    return dates


def create_dates_dataset(html_dates):
    date_ids = [li['data-value'] for li in html_dates]
    dates = [li.text.strip() for li in html_dates]
    dataset = pd.DataFrame(data={'date': dates, 'date_id': date_ids})
    dataset['date'] = pd.to_datetime(dataset['date'], format='%d %B %Y')
    dataset.sort_values('date', ignore_index=True, inplace=True)
    return dataset

# ------------------------
# Scraping Ranking por Fecha
# ------------------------
async def get_rank_page(date_id, session):
    async with session.get(f'{FIFA_URL}/{date_id}/') as response:
        page = await response.text()
        if response.status == 200:
            return {'page': page, 'id': date_id}
        else:
            return False

def scrapy_rank_table(page, date):
    rows = BeautifulSoup(page, 'html.parser', parse_only=SoupStrainer('tbody')).find_all('tr')
    table = []
    for row in rows:
        table.append({
            'id': int(row['data-team-id']),
            'country_full': row.find('span', {'class': 'fi-t__nText'}).text,
            'rank': int(row.find('td', {'class': 'fi-table__rank'}).text),
            'total_points': int(row.find('td', {'class': 'fi-table__points'}).text),
            'rank_date': date
        })
    return table

async def parse_ranks(pages_df):
    fifa_ranking = pd.DataFrame(columns=['id', 'rank', 'country_full', 'total_points', 'rank_date'])
    task_parse = []
    async with aiohttp.ClientSession() as session:
        for date_id in pages_df.date_id.tail(1):  # Solo la fecha más reciente
            task_parse.append(asyncio.create_task(get_rank_page(date_id, session)))

        for task in asyncio.as_completed(task_parse):
            page = await task
            if not task:
                continue
            date_ranking = scrapy_rank_table(page['page'], pages_df[pages_df.date_id == page['id']].date.iloc[0])
            fifa_ranking = pd.concat([fifa_ranking, pd.DataFrame(date_ranking)], ignore_index=True)
    return fifa_ranking

# ------------------------
# Streamlit App
# ------------------------
st.set_page_config(page_title="Ranking FIFA", layout="centered")
st.title("🏆 Ranking FIFA Masculino")

if 'ranking_df' not in st.session_state:
    with st.spinner('Obteniendo datos desde FIFA.com...'):
        html_dates = get_dates_html()
        fechas_df = create_dates_dataset(html_dates)
        ranking_df = asyncio.run(parse_ranks(fechas_df))
        st.session_state['ranking_df'] = ranking_df
else:
    ranking_df = st.session_state['ranking_df']

st.subheader("🌐 Ranking actual")
st.dataframe(ranking_df)

seleccion = st.selectbox("Seleccioná una selección:", ranking_df['country_full'].unique())
fila = ranking_df[ranking_df['country_full'] == seleccion].iloc[0]
st.metric("Posición FIFA", fila['rank'])
st.metric("Puntos", fila['total_points'])
