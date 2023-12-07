import csv
import logging
import datetime as dt
from prettytable import PrettyTable

from constants import BASE_DIR, DATETIME_FORMAT


def control_output(results, cli_args):
    output = cli_args.output
    if output == 'pretty':
        pretty_output(results)
    elif output == 'file':
        file_output(results, cli_args)
    else:
        default_output(results)


def default_output(results):
    for row in results:
        print(*row)


def pretty_output(results):
    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'
    table.add_rows(results[1:])
    print(table)


def file_output(results, cli_args):
    results_dir = BASE_DIR / 'results'
    results_dir.mkdir(exist_ok=True)
    parser_mode = cli_args.mode
    now = dt.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)
    file_name = f'{parser_mode}_{now_formatted}.csv'
    file_path = results_dir / file_name
    with open(file_path, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, dialect='unix')
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
