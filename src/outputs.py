# outputs.py
import csv
import logging
import datetime as dt
from prettytable import PrettyTable

from constants import BASE_DIR, DATETIME_FORMAT


def control_output(results, cli_args):
    # Чтобы не обращаться дважды к атрибуту объекта в условиях if, elif,
    # сохраним значение в переменную.
    output = cli_args.output
    if output == 'pretty':
        # Вывод данных в PrettyTable.
        pretty_output(results)
    elif output == 'file':
        # Вывод данных в файл csv. Саму функцию напишем позже.
        file_output(results, cli_args)
    else:
        # Вывод данных по умолчанию — в терминал построчно.
        default_output(results)


def default_output(results):
    # Печатаем список results построчно.
    for row in results:
        print(*row)


def pretty_output(results):
    # Инициализируем объект PrettyTable.
    table = PrettyTable()
    # В качестве заголовков устанавливаем первый элемент списка.
    table.field_names = results[0]
    # Выравниваем всю таблицу по левому краю.
    table.align = 'l'
    # Добавляем все строки, начиная со второй (с индексом 1).
    table.add_rows(results[1:])
    # Печатаем таблицу.
    print(table)


def file_output(results, cli_args):
    results_dir = BASE_DIR / 'results'
    results_dir.mkdir(exist_ok=True)
    parser_mode = cli_args.mode
    now = dt.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)
    file_name = f'{parser_mode}_{now_formatted}.csv'
    file_path = results_dir / file_name
    # Отсюда начинается новый код.
    # Через контекстный менеджер открываем файл по сформированному ранее пути
    # в режиме записи 'w', в нужной кодировке utf-8.
    with open(file_path, 'w', encoding='utf-8') as f:
        # Создаём «объект записи» writer.
        writer = csv.writer(f, dialect='unix')
        # Передаём в метод writerows список с результатами парсинга.
        writer.writerows(results)

    logging.info(f'file was downloaded to {file_path}')


# делаем вывод таблицы
def output_table(table_with_results: dict):
    res_tb = PrettyTable()
    res_tb.field_names = (
        'Статус',
        'Количество',
    )
    res_tb.add_rows([(k, v) for k, v in table_with_results.items()])
    res_tb.add_row(('Total', sum(table_with_results.values())))
    return res_tb


def output_in_file(results):
    dow_dir = BASE_DIR / 'results'
    dow_dir.mkdir(exist_ok=True)
    time_now = dt.datetime.now()
    now_form = time_now.strftime(DATETIME_FORMAT)
    file_name = f'{now_form}.csv'
    file_path = dow_dir / file_name

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(results)

