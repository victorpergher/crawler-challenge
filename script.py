from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib import robotparser

import socket

from bs4 import BeautifulSoup
import jsonlines
import sqlite3

# NOTE lib's to CLI
from tabulate import tabulate
import click

import xlsxwriter

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

def insertData(name_company, name_machine, cpu, ram, storage, bandwidth, price_hour, price_monthly):
    ram = ram.replace('GB', '')
    if (ram.find('MB') > -1):
        ram = ram.replace('MB', '')
        ram = int(ram) / 1000

    bandwidth = bandwidth.replace('TB', '')
    storage = storage.replace('\n', '')
    storage = storage.replace(',', '')
    price_hour = price_hour.replace('$', '')
    price_hour = price_hour.replace('/', '')
    price_hour = price_hour.replace('hr', '')
    price_hour = price_hour.replace('h', '')
    price_hour = price_hour.replace(',', '')
    if (price_monthly == ''):
        price_monthly = float(price_hour) * 30
    else:
        price_monthly = price_monthly.replace('$', '')
        price_monthly = price_monthly.replace('/', '')
        price_monthly = price_monthly.replace('mo', '')
        price_monthly = price_monthly.replace(',', '')
    sql = f"SELECT count(*) AS qtd FROM services WHERE name_machine = '{name_machine}' AND name_company = '{name_company}'"
    cursor.execute(sql)
    result = cursor.fetchone()
    if (result[0] == 0):
        sql = f"""
        INSERT INTO services (
            name_company,
            name_machine,
            cpu,
            ram,
            storage,
            bandwidth,
            price_hour,
            price_monthly
        )
        VALUES (
            "{name_company}",
            "{name_machine}",
            "{cpu}",
            {ram},
            "{storage}",
            "{bandwidth}",
            {price_hour},
            {price_monthly}
        )
        """
    else:
        sql = f"""
        UPDATE services SET
            cpu           = "{cpu}",
            ram           = {ram},
            storage       = "{storage}",
            bandwidth     = "{bandwidth}",
            price_hour    = {price_hour},
            price_monthly = {price_monthly}
        WHERE
            name_machine  = "{name_machine}" AND
            name_company  = "{name_company}"
            """
    print('----------------')
    print(sql)
    cursor.execute(sql)
    conn.commit()

def getDataPacket():
    req = Request('https://www.packet.com/cloud/servers/', headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36'})
    html = urlopen(req)

    bsObj = BeautifulSoup(html.read(), features="lxml")
    items = bsObj.findAll("div", {"class":"tbl_row_content"})
    for item in items:
        name_company = 'Packet'
        name_machine = item.find("div", {"class":"tbl_col-config"}).text.strip()
        cpu = item.find("div", {"class":"tbl_col-processor"}).text.strip()
        cpu = cpu + ' ' + item.find("div", {"class":"tbl_col-cores"}).text.strip()
        ram = item.find("div", {"class":"tbl_col-ram"}).text.strip()
        storage = item.find("div", {"class":"tbl_col-storage"}).text.strip()
        bandwidth = ''
        price_hour = item.find("div", {"class":"tbl_col-price"}).text.strip()
        price_monthly = ''
        insertData(
            name_company,
            name_machine,
            cpu,
            ram,
            storage,
            bandwidth,
            price_hour,
            price_monthly
        )
    html.close()

def getDataVultr():
    req = Request('https://www.vultr.com/pricing/', headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36'})
    html = urlopen(req)
    bsObj = BeautifulSoup(html.read(), features="lxml")
    items = bsObj.findAll("div", {"class":"pt__row"})
    name_company = 'Vultr' # Nome do servico/site
    for index, item in enumerate(items):
        name_machine = 'VC2' + str(index)
        cpu = item.find("div", {"class":"pt__col--cpu"}).text.strip()
        ram = item.find("div", {"class":"pt__col--memory"}).text.strip()
        storage = item.find("div", {"class":"pt__col--storage"})
        storage = storage.find("b").text

        bandwidth = item.find("div", {"class":"pt__col--bandwidth"})
        bandwidth = bandwidth.find("b").text.strip()
        price = item.find("div", {"class":"pt__col--price"})
        price_hour = price.find("span", {"class": "pt__price--hourly"}).text.strip()
        price_monthly = price.find("span", {"class": "pt__price--monthly"}).text.strip()
        insertData(
            name_company,
            name_machine,
            cpu,
            ram,
            storage,
            bandwidth,
            price_hour,
            price_monthly
            )

def getDataDigitalOcean():
    def insertService(droplet):
        trs = droplet.findAll('tr')
        for index, tr in enumerate(trs):
            td = tr.findAll('td')
            ram = td[0].text.strip()
            cpu = td[1].text.strip()
            storage = td[2].text.strip()
            bandwidth = td[3].text.strip()
            price = td[4].text
            price_monthly_init = price.find('$')
            price_hour_init = price.rfind('$')
            price_monthly = price[price_monthly_init: price_hour_init-1]
            price_hour = price[price_hour_init: -1]
            insertData(
                name_company,
                name_machine + ' ' + str(index),
                cpu,
                ram,
                storage,
                bandwidth,
                price_hour,
                price_monthly
            )

    req = Request('https://www.digitalocean.com/pricing/#droplet', headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36'})
    html = urlopen(req)
    bsObj = BeautifulSoup(html.read(), features="lxml")
    items = bsObj.findAll("table", {"class":"PricingTable"})
    name_company = 'DigitalOcean' # Nome do servico/site
    droplet = items[0] # Primeira tabela de preços - Standard Droplets
    droplet = list(droplet)[3] # Somente o bloco com os tr's dos serviços
    name_machine = 'Standard Droplets'
    insertService(droplet)

    droplet = items[1] # Segunda tabela de preços - General Purpose
    droplet = list(droplet)[3] # Somente o bloco com os tr's dos serviços
    name_machine = 'General Purpose Droplets'
    insertService(droplet)

# NOTE Resetar o banco de dados - INICIO
# sql = 'drop table if exists services'
# cursor.execute(sql)
# NOTE Resetar o banco de dados - FIM

# NOTE Criar tabela - INICIO
sql = """ CREATE TABLE iF NOT EXISTS services (
                name_company TEXT,
                name_machine TEXT,
                cpu TEXT,
                ram INT,
                storage TEXT,
                bandwidth INT,
                price_hour REAL,
                price_monthly REAL) """

cursor.execute(sql)
# NOTE Criar tabela - FIM

@click.command()
@click.option('--show', default=0, help='Show data on terminal.')
@click.option('--export', default=0, help='Save data on xls.')
@click.option('--update', default=1, help='Update database')

def cli(show, export, update):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()


    if (update):
        click.echo('Updating data - Packet')
        getDataPacket()
        click.echo('Updating data - Vultr')
        getDataVultr()
        click.echo('Updating data - DigitalOcean')
        getDataDigitalOcean()

    if (show):
        click.echo('Show data on terminal!')
        cursor.execute("""
        SELECT
            name_company  AS 'Serviço/site',
            name_machine  AS 'Nome da máquina',
            cpu           AS 'CPUs',
            ram           AS 'Memória',
            storage       AS 'Storage',
            bandwidth     AS 'Qtd bandwidth por mês (TB)',
            price_hour    AS 'Valor por hora ($)',
            price_monthly AS 'Valor por mês ($)'
        FROM
            services
        """)
        result = cursor.fetchall()

        col_name_list = [tuple[0] for tuple in cursor.description]
        print(tabulate(result, headers=col_name_list))

    if (export):
        click.echo('Save data on xls!')
        cursor.execute("""
        SELECT
            name_company  AS 'Nome do serviço/site',
            name_machine  AS 'Nome da máquina',
            cpu           AS 'CPUs',
            ram           AS 'Memória',
            storage       AS 'Storage',
            bandwidth     AS 'Quantidade de transfer/bandwidth por mês',
            price_hour    AS 'Valor por hora ($)',
            price_monthly AS 'Valor por mês ($)'
        FROM
            services
        """)
        result = cursor.fetchall()
        workbook = xlsxwriter.Workbook('data.xlsx')
        worksheet = workbook.add_worksheet()
        col_name_list = [tuple[0] for tuple in cursor.description]
        cell_format = workbook.add_format({'bold': True})
        for index, item in enumerate(col_name_list):
            worksheet.write(0, index, item, cell_format)
        for index, item in enumerate(result):
            for idx, ivl in enumerate(item):
                worksheet.write(index+1, idx, ivl)
        workbook.close()

if __name__ == '__main__':
    cli()
