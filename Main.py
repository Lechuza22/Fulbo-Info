import streamlit as st
import pandas as pd
import datetime
import asyncio
import aiohttp
import requests as r
from bs4 import BeautifulSoup, SoupStrainer
import logging
import os

# Configurar logging
logger = logging.getLogger('fifa_logger')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.WARNING)

FIFA_URL = 'https://www.fifa.com/fifa-world-ranking/ranking-table/men/rank'
FIRST_DATE = 'id1'

@st.cache_data
def get_dates_html():
    page_source = r.get(f'{FIFA_URL}/{FIRST_DATE}/')
    page_source.raise_for_status()
    dates = BeautifulSoup(page_source.text, 'html.parser', parse_only=SoupStrainer('li', attrs={'class': 'fi-ranking-schedule__nav__item'}))
    return dates

def create_dates_dataset(html_dates):
    date_ids = [li['data-value'] for li in html_dates]
    dates = [li.text.strip() for li in html_dates]
    dataset = pd.DataFrame(data={'date': dates, 'date_id': date_ids})
    dataset['date'] = pd.to_datetime(dataset['date'], format='%d %B %Y')
    dataset.sort_values('date', ignore_index=True, inplace=True)
    return dataset

async def get_rank_page(date_id, session):
    async with session.get(f'{FIFA_URL}/{date_id}/') as response:
        page = await response.text()
        if response.status == 200:
            return {'page': page, 'id': date_id}
        else:
            return None

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
    fifa_ranking = pd.DataFrame()
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(get_rank_page(row.date_id, session)) for _, row in pages_df.iterrows()]
        for task in asyncio.as_completed(tasks):
            page = await task
            if page:
                date = pages_df[pages_df.date_id == page['id']].date.iloc[0]
                data = scrapy_rank_table(page['page'], date)
                fifa_ranking = pd.concat([fifa_ranking, pd.DataFrame(data)], ignore_index=True)
    return fifa_ranking

def run_scraper():
    dates_html = get_dates_html()
    dates_df = create_dates_dataset(dates_html).tail(1)  # solo la fecha más reciente para rendimiento
    fifa_ranking_df = asyncio.run(parse_ranks(dates_df))
    return fifa_ranking_df

# ==== Streamlit App ====
st.set_page_config(page_title="🏆 Ranking FIFA", layout="centered")
st.title("🌍 Ranking FIFA Masculino (última actualización)")

if st.button("🔄 Actualizar Ranking FIFA"):
    with st.spinner("Obteniendo datos en tiempo real desde FIFA..."):
        df = run_scraper()
        st.success("Ranking actualizado correctamente")
        st.dataframe(df)
else:
    st.info("Presiona el botón para obtener el ranking más reciente de FIFA.")
