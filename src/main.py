import re
from urllib.parse import urljoin
import logging

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from constants import BASE_DIR, MAIN_DOC_URL, MAIN_PEP_URL, EXPECTED_STATUS
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_response, find_tag, parse_table


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, 'lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    section_by_python = div_with_ul.find_all('li',
                                             attrs={'class': 'toctree-l1'})

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]

    for section in tqdm(section_by_python):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)

        response = get_response(session, version_link)
        if response is None:
            continue

        soup = BeautifulSoup(response.text, 'lxml')

        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')

        results.append((version_link, h1.text, dl_text))

    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')

    sidebar = find_tag(soup, 'nav', attrs={'class': 'menu'})
    ul_tags = sidebar.find_all('ul')

    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Ничего не нашлось')

    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'

    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append((link, version, status))

    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, 'lxml')

    table = find_tag(soup, 'table', attrs={'class': 'docutils'})

    pdf_a4_tag = find_tag(
        table, 'a', attrs={'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]

    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename

    response = get_response(session, archive_url)
    if response is None:
        return

    with open(archive_path, 'wb') as file:
        file.write(response.content)

    logging.info(f'Архив был загружен и сохранен: {archive_path}')


def pep(session):
    response = get_response(session, MAIN_PEP_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, 'lxml')
    tables_tag = soup.find_all('table')

    pep_links = []

    for table_tag in tables_tag:
        if 'PEP' not in table_tag.thead.text:
            continue
        pep_links += parse_table(table_tag.tbody)

    if not pep_links:
        raise Exception('Ссылок не нашлось')

    results = [('Статус', 'Количество')]
    counts = {}
    for preview_status, pep_link in tqdm(pep_links):
        response = get_response(session, pep_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        current_status = soup.find(
            string='Status').parent.next_sibling.next_sibling.text
        status_count = counts.get(current_status, 0)
        counts[current_status] = status_count + 1
        if current_status not in EXPECTED_STATUS[preview_status]:
            logging.info(f'Несовпадающие статусы:\n{pep_link}\n'
                         f'Статус в карточке: {current_status}\n'
                         f'Ожидаемые статусы: '
                         f'{EXPECTED_STATUS[preview_status]}')

    for status, count in counts.items():
        results.append((status, count))
    results.append(('Total', len(pep_links)))

    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    try:
        configure_logging()

        arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
        args = arg_parser.parse_args()

        logging.info('Парсер запущен')
        logging.info(f'Аргументы командной строки: {args}')

        session = requests_cache.CachedSession()
        if args.clear_cache:
            session.cache.clear()

        parser_mode = args.mode
        results = MODE_TO_FUNCTION[parser_mode](session)

        if results:
            control_output(results, args)

        logging.info('Парсер завершил работу')

    except Exception as e:
        logging.exception(e)


if __name__ == '__main__':
    main()
