import logging
from urllib.parse import urljoin

from requests import RequestException

from exceptions import ParserFindTagException
from constants import MAIN_PEP_URL


def get_response(session, url):
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        return response
    except RequestException:
        logging.exception(
            f'Возникла ошибка при загрузке страницы: {url}',
            stack_info=True
        )


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)

    return searched_tag


def parse_table(table):
    try:
        tr_tags = table.find_all('tr')
        pep_links = []
        for tr_tag in tr_tags:
            preview_status = tr_tag.td.text[1:]
            a_tag = tr_tag.td.next_sibling.next_sibling.a
            href = a_tag['href']
            pep_links.append((preview_status, urljoin(MAIN_PEP_URL, href)))
        return pep_links
    except Exception as e:
        logging.exception(f'Возникла ошибка при обработке таблицы: {e}')
