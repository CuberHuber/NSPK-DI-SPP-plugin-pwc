"""
Нагрузка плагина SPP

1/2 документ плагина
"""
import datetime
import logging
import re
import time

import dateutil.parser
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from src.spp.types import SPP_document


class PriceWaterhouseCooprs:
    """
    Класс парсера плагина SPP

    :warning Все необходимое для работы парсера должно находится внутри этого класса

    :_content_document: Это список объектов документа. При старте класса этот список должен обнулиться,
                        а затем по мере обработки источника - заполняться.


    """

    SOURCE_NAME = 'pwc'
    _content_document: list[SPP_document]

    HOST = 'https://www.pwc.com'

    def __init__(self, webdriver, max_count_documents: int = None, last_document: SPP_document = None, *args, **kwargs):
        """
        Конструктор класса парсера

        По умолчанию внего ничего не передается, но если требуется (например: driver селениума), то нужно будет
        заполнить конфигурацию
        """
        # Обнуление списка
        self._content_document = []
        self._driver = webdriver
        self._max_count_documents = max_count_documents
        self._last_document = last_document

        # Логер должен подключаться так. Вся настройка лежит на платформе
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Parser class init completed")
        self.logger.info(f"Set source: {self.SOURCE_NAME}")
        ...

    def content(self) -> list[SPP_document]:
        """
        Главный метод парсера. Его будет вызывать платформа. Он вызывает метод _parse и возвращает список документов
        :return:
        :rtype:
        """
        self.logger.debug("Parse process start")
        try:
            self._parse()
        except Exception as e:
            self.logger.debug(f'Parsing stopped with error: {e}')
        else:
            self.logger.debug("Parse process finished")
        return self._content_document

    def _parse(self):
        """
        Метод, занимающийся парсингом. Он добавляет в _content_document документы, которые получилось обработать
        :return:
        :rtype:
        """
        # HOST - это главная ссылка на источник, по которому будет "бегать" парсер
        self.logger.debug(F"Parser enter to {self.HOST}")

        # ========================================
        # Тут должен находится блок кода, отвечающий за парсинг конкретного источника
        # -
        self._driver.set_page_load_timeout(40)

        markets_link = 'https://www.pwc.com/gx/en/industries/consumer-markets/publications.html'
        industries_link = 'https://www.pwc.com/gx/en/industries/tmt/publications.html'
        research_link = 'https://www.pwc.com/gx/en/industries/financial-services/publications.html'

        docs = []
        docs.extend(self._collect_links_from_publications_page(markets_link))
        docs.extend(self._collect_links_from_publications_page(industries_link))
        # docs.extend(self._collect_links_from_publications_page(research_link))

        for doc in docs:
            self._parse_publication(doc)
        # ---
        # ========================================

    def _collect_links_from_publications_page(self, url: str):
        self._initial_access_source(url)
        self.logger.debug(f'Start collect publications from {url}')

        docs = []

        try:
            results_e = self._driver.find_element(By.CLASS_NAME, 'results').text
            results = int(re.match(r'(\d+).*', results_e).groups()[0])
            print(results)
        except Exception as e:
            self.logger.error(e)

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # ВОТ ТУТ НУЖНО ВСТАВИТЬ ДОКАЧКУ ФАЙЛОВ ПРИ ПОМОЩИ КНОКИ MORE.
        # ............................................................
        # Сейчас статьи не докачиваются...
        time.sleep(6)
        articles = self._driver.find_elements(By.CLASS_NAME, 'collection__item-link')
        print(len(articles))


        for index, article in enumerate(articles):
            # Ограничение парсинга до установленного параметра self.max_count_documents
            if index >= self._max_count_documents:
                self.logger.debug(f'Max count articles reached ({self._max_count_documents})')
                break

            try:
                href = article.get_attribute('href')
                date = article.find_element(By.TAG_NAME, 'time').text
                title = article.find_element(By.TAG_NAME, 'h4').text
                abstract = None

                try:
                    abstract = article.find_element(By.CLASS_NAME, 'paragraph').text
                except: pass

                document = SPP_document(None, title, abstract, None, href, None, None, dateutil.parser.parse(date), None)
                self.logger.debug(f'find new article {href}')
                docs.append(document)
            except Exception as e:
                self.logger.error(e)

        return docs

    def _parse_publication(self, doc: SPP_document):
        self.logger.debug(f'Start parse publications at {doc.web_link}')
        try:
            self._initial_access_source(doc.web_link)
            time.sleep(2)

            text = self._driver.find_element(By.CLASS_NAME, 'container').text
            doc.text = text
            doc.load_date = datetime.datetime.now()

        except Exception as e:
            self.logger.error(e)

        self.find_document(doc)


    def _initial_access_source(self, url: str, delay: int = 2):
        self._driver.get(url)
        self.logger.debug('Entered on web page '+url)
        time.sleep(delay)
        self._agree_cookie_pass()

    def _agree_cookie_pass(self):
        """
        Метод прожимает кнопку agree на модальном окне
        """
        cookie_agree_xpath = '//*[@id="onetrust-accept-btn-handler"]'

        try:
            cookie_button = self._driver.find_element(By.XPATH, cookie_agree_xpath)
            if WebDriverWait(self._driver, 5).until(ec.element_to_be_clickable(cookie_button)):
                cookie_button.click()
                self.logger.debug(F"Parser pass cookie modal on page: {self._driver.current_url}")
        except NoSuchElementException as e:
            self.logger.debug(f'modal agree not found on page: {self._driver.current_url}')

    @staticmethod
    def _find_document_text_for_logger(doc: SPP_document):
        """
        Единый для всех парсеров метод, который подготовит на основе SPP_document строку для логера
        :param doc: Документ, полученный парсером во время своей работы
        :type doc:
        :return: Строка для логера на основе документа
        :rtype:
        """
        return f"Find document | name: {doc.title} | link to web: {doc.web_link} | publication date: {doc.pub_date}"

    def find_document(self, _doc: SPP_document):
        """
        Метод для обработки найденного документа источника
        """
        if self._last_document and self._last_document.hash == _doc.hash:
            raise Exception(f"Find already existing document ({self._last_document})")

        if self._max_count_documents and len(self._content_document) >= self._max_count_documents:
            raise Exception(f"Max count articles reached ({self._max_count_documents})")

        self._content_document.append(_doc)
        self.logger.info(self._find_document_text_for_logger(_doc))
