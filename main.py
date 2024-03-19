import datetime
import io

from selenium import webdriver
from logging import config
from pwc import PriceWaterhouseCooprs
import pickle
import pandas

from src.spp.types import SPP_document

config.fileConfig('dev.logger.conf')


def driver():
    """
    Selenium web driver
    """
    options = webdriver.ChromeOptions()

    # Параметр для того, чтобы браузер не открывался.
    options.add_argument('headless')

    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")

    return webdriver.Chrome(options)


def to_dict(doc: SPP_document) -> dict:
    return {
        'title': doc.title,
        'abstract': doc.abstract,
        'text': doc.text,
        'web_link': doc.web_link,
        'local_link': doc.local_link,
        'other_data': '',
        'pub_date': str(doc.pub_date.timestamp()) if doc.pub_date else '',
        'load_date': str(doc.load_date.timestamp()) if doc.load_date else '',
    }

def dump():
    with open('backup/documents.backup.pkl', 'rb') as file:
        return io.BytesIO(file.read())

doc = SPP_document(doc_id=None, title='Valley Forge Fabrics: Weaving in cloud-based efficiency from quote to install', abstract='What is cloud operational efficiency? For VFF, it’s a Microsoft solution that streamlines operations, improves customer experiences and supports growth.', text=None, web_link='https://www.pwc.com/gx/en/ghost/valley-forge-fabrics-cloud-efficiency.html', local_link=None, other_data=None, pub_date=datetime.datetime(2023, 11, 15, 0, 0), load_date=datetime.datetime(2024, 3, 19, 13, 53, 25, 455015))

parser = PriceWaterhouseCooprs(driver(), 5, doc)
docs: list[SPP_document] = parser.content()
#
# try:
#     with open('backup/documents.backup.pkl', 'wb') as file:
#         pickle.dump(docs, file)
# except Exception as e:
#     print(e)
#
# try:
#     dataframe = pandas.DataFrame.from_records([to_dict(d) for d in docs])
#     dataframe.to_csv('out/documents.csv')
# except Exception as e:
#     print(e)

print(*docs, sep='\n\r\n')
