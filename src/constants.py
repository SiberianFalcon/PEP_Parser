from pathlib import Path

BASE_DIR = Path(__file__).parent
MAIN_DOC_URL = 'https://docs.python.org/3/'
MAIN_LINK = 'https://peps.python.org/'

EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}

CONST_NAME_PRETTY = 'pretty'
CONST_NAME_PEP = 'pep'
CONST_NAME_FILE = 'file'
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
DT_FORMAT = '%d.%m.%Y %H:%M:%S'
REGEX_FOR_FUNC_DOWNLOAD = r'.+pdf-a4\.zip$'
REGEX_FOR_FUNC_PEP = r'pep-\d{4}/$'
LOG_FORMAT = '"%(asctime)s -[%(levelname)s] - %(message)s"'
