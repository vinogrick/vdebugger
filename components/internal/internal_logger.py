import logging

class CustomFormatter(logging.Formatter):

    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: f'[%(asctime)s]--[%(levelname)s]--[%(filename)s:%(lineno)d]: %(message)s',
        logging.INFO: f'[%(asctime)s]--[{green}%(levelname)s{reset}]--[%(filename)s:%(lineno)d]: %(message)s',
        logging.WARNING: f'[%(asctime)s]--[{yellow}%(levelname)s{reset}]--[%(filename)s:%(lineno)d]: %(message)s',
        logging.ERROR: f'[%(asctime)s]--[{red}%(levelname)s{reset}]--[%(filename)s:%(lineno)d]: %(message)s',
        logging.CRITICAL: f'[%(asctime)s]--[{bold_red}%(levelname)s{reset}]--[%(filename)s:%(lineno)d]: %(message)s'
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def getLogger(module):
    logger = logging.getLogger(module)
    if logger.hasHandlers():
        return logger
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(CustomFormatter())
    logger.addHandler(ch)
    return logger
