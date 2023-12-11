import re
import logging
from urllib.parse import urljoin

import requests_cache
from tqdm import tqdm
from bs4 import BeautifulSoup

from constants import (
    BASE_DIR, MAIN_DOC_URL, MAIN_LINK, EXPECTED_STATUS,
    REGEX_FOR_FUNC_DOWNLOAD, REGEX_FOR_FUNC_PEP
)
from configs import configure_argument_parser, configure_logging
from exceptions import ParserFindTagException
from outputs import control_output
from utils import find_tag, get_response, response_with_soup


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = response_with_soup(session, whats_new_url)
    div_with_li = find_tag(response, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_li.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )

    result = []
    for section in tqdm(sections_by_python, desc='парсим ссылки'):
        result = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
        ver_a_tag = find_tag(section, 'a')
        href = ver_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = response_with_soup(session, version_link)
        h1 = find_tag(response, 'h1')
        dl = find_tag(response, 'dl')
        result.append(version_link)
        result.append(h1.text)
        result.append(dl.text)

    return result


def latest_versions(session):
    response = response_with_soup(session, MAIN_DOC_URL)

    sidebar = find_tag(
        response, 'div', attrs={'class': 'sphinxsidebarwrapper'}
    )
    ul_tags = sidebar.find_all('ul')

    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise ParserFindTagException('Ничего не нашлось')

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
    return results


def download(session):
    download_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = response_with_soup(session, download_url)

    main_page = find_tag(response, 'div', attrs={'role': 'main'})
    table = find_tag(main_page, 'table', attrs={'class': 'docutils'})
    pdf_a4_tag = find_tag(
        table, 'a', attrs={
            'href': re.compile(REGEX_FOR_FUNC_DOWNLOAD)
        }
    )

    archive_url = urljoin(download_url, pdf_a4_tag['href'])
    filename = archive_url.split('/')[-1]

    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename

    response = get_response(session, archive_url)

    with open(archive_path, 'wb') as file:
        file.write(response.content)

    logging.info(f'zip_file was downloaded to {archive_path}')


def pep(session):

    result_table = {
        'Accepted': 0,
        'Active': 0,
        'Deferred': 0,
        'Final': 0,
        'Provisional': 0,
        'Rejected': 0,
        'Superseded': 0,
        'Withdrawn': 0,
        'Draft': 0,
    }

    response = response_with_soup(session, MAIN_LINK)

    # разбиваем на группы
    start_pars = response.find_all(
        'section', id='numerical-index'
    )

    # список статусов
    status_list = []

    # разбиваем группу на сроки для поиска
    strings_in_group = start_pars[0].find_all('tr')
    for x in strings_in_group:

        # вытаскиваем статус из левой колонки
        search_status = x.find('abbr')
        if search_status is not None:
            status_list.append(search_status.text)

        # вытаскиваем половинку ссылки ведущий к доке по каждому пепу
        search_links = x.find(
            'a', attrs={'class': 'pep reference internal'}
        )
        if (search_links is not None
                and re.match(REGEX_FOR_FUNC_PEP, search_links['href'])):
            need_link = urljoin(MAIN_LINK, search_links['href'])
            get_pep_doc = BeautifulSoup(
                session.get(need_link).text, features='lxml'
            )

            # шагаем до строки статуса по тегам в доке
            # и берём статус пепа
            get_pep_tag = get_pep_doc.find('dt')
            status_in_doc = None
            while True:
                get_pep_tag = get_pep_tag.find_next()
                if get_pep_tag.text == 'Status:':
                    status_in_doc = get_pep_tag.find_next().find_next().text
                    break

            try:
                if (status_in_doc in EXPECTED_STATUS[search_status.text[1:]]
                        or status_in_doc in result_table.keys()):

                    result_table[status_in_doc] = result_table[
                                                      status_in_doc] + 1
                else:
                    if result_table.get(status_in_doc) is not None:
                        result_table[status_in_doc] = 0

                    result_table[
                        status_in_doc] = result_table[status_in_doc] + 1
                    result_table[
                        EXPECTED_STATUS[search_status.text[1:]][0]] = (
                            result_table[
                                EXPECTED_STATUS[search_status.text[1:]][0]] - 1
                        )

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

    return result_table


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('parser_started')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'аргумент запуска функции {args}')

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        control_output(results, args)
    logging.info('parser finished work')


if __name__ == '__main__':
    main()
