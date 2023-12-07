from pathlib import Path
import re
from urllib.parse import urljoin
import logging

import requests_cache
from tqdm import tqdm
from bs4 import BeautifulSoup
from prettytable import PrettyTable

from constants import (
    BASE_DIR, MAIN_DOC_URL, MAIN_LINK,
    EXPECTED_STATUS, RESULT_TABLE
)
from configs import configure_argument_parser, configure_logging
from exceptions import StatusNotMatch
from outputs import control_output, output_table, output_in_file
from utils import get_response, find_tag


########################################
from requests_cache import CachedSession


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_li = find_tag(soup, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_li.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )

    result = []
    for section in tqdm(sections_by_python, desc='парсим сылОчки'):
        result = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
        ver_a_tag = find_tag(section, 'a')
        href = ver_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        result.append((version_link, h1.text, dl.text))

    return result


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')

    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')

    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Ничего не нашлось')

    results = []
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append(
            (link, version, status)
        )
    for row in results:
        print(*row)


def download(session):
    download_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, download_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')

    main_page = find_tag(soup, 'div', attrs={'role': 'main'})
    table = find_tag(main_page, 'table', attrs={'class': 'docutils'})
    pdf_a4_tag = find_tag(table, 'a', attrs={
        'href': re.compile(r'.+pdf-a4\.zip$')})

    archive_url = urljoin(download_url, pdf_a4_tag['href'])
    filename = archive_url.split('/')[-1]

    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename

    response = session.get(archive_url)

    with open(archive_path, 'wb') as file:
        file.write(response.content)

    logging.info(f'zip_file was downloaded to {archive_path}')


def pep(session):
        session = CachedSession()
        response = session.get(MAIN_LINK)
        soup = BeautifulSoup(response.text, features='lxml')

        # разбиваем на группы
        start_pars = soup.find_all(
            'section', id='numerical-index'
        )

        # список статусов
        status_list = []

        # проходимся вглубь каждой группы
        for i in tqdm(start_pars):

            # разбиваем группу на сроки для поиска
            strings_in_group = i.find_all('tr')
            for x in strings_in_group:

                # вытаскиваем статус из левой колонки
                search_status = x.find('abbr')
                if search_status is not None:
                    status_list.append(search_status.text)

                # вытаскиваем половинку ссылки ведущий к доке по каждому пепу
                search_links = x.find(
                    'a', attrs={'class': 'pep reference internal'}
                )
                if search_links is not None \
                        and re.match(r'pep-\d{4}/$', search_links['href']):
                    need_link = urljoin(MAIN_LINK, search_links['href'])
                    get_pep_doc = BeautifulSoup(
                        session.get(need_link).text, features='lxml'
                    )

                    # шагаем до строки статуса по тегам в доке и берём статус пепа
                    get_pep_tag = get_pep_doc.find('dt')
                    status_in_doc = None
                    while True:
                        get_pep_tag = get_pep_tag.find_next()
                        if get_pep_tag.text == 'Status:':
                            status_in_doc = get_pep_tag.find_next() \
                                .find_next().text
                            break
                    try:
                        if status_in_doc \
                                in EXPECTED_STATUS[search_status.text[1:]]:

                            RESULT_TABLE[status_in_doc] = \
                                RESULT_TABLE[status_in_doc] + 1

                        else:
                            RESULT_TABLE[status_in_doc] = \
                                RESULT_TABLE[status_in_doc] + 1

                    except Exception:
                        logging.info(
                            f'''
                            Несовпадающие статусы:
                            {need_link}
                            Статус в карточке: {status_in_doc}
                            Ожидаемые статусы: {
                            EXPECTED_STATUS[search_status.text[1:]]}
                            '''
                        )



            output_in_file(str(output_table(RESULT_TABLE)))



MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('parser_started')
    # Конфигурация парсера аргументов командной строки —
    # передача в функцию допустимых вариантов выбора.
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    # Считывание аргументов из командной строки.
    args = arg_parser.parse_args()
    logging.info(f'аргумент запуска функции {args}')

    session = requests_cache.CachedSession()
    # Если был передан ключ '--clear-cache', то args.clear_cache == True.
    if args.clear_cache:
        # Очистка кеша.
        session.cache.clear()

    # Получение из аргументов командной строки нужного режима работы.
    parser_mode = args.mode
    # Поиск и вызов нужной функции по ключу словаря.
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        control_output(results, args)
    logging.info('parser finished work')


if __name__ == '__main__':
    main()
