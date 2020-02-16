import logging
import sys


class SplitFilter(object):
    def __init__(self, level):
        self.__level = level

    def filter(self, logRecord):
        return logRecord.levelno <= self.__level


class Logging:
    def __init__(self, name: str, level: str = 'NOTSET'):
        level = getattr(logging, level.upper())
        self._logger = logging.getLogger()
        self._logger.setLevel(level)

        stdout = logging.StreamHandler(sys.stdout)
        stdout.setLevel(logging.DEBUG)
        stdout.addFilter(SplitFilter(logging.INFO))
        stdout.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self._logger.addHandler(stdout)

        stderr = logging.StreamHandler(sys.stderr)
        stderr.setLevel(logging.WARNING)
        stderr.addFilter(SplitFilter(logging.WARNING))
        stderr.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self._logger.addHandler(stderr)

    def critical(self, msg: str):
        return self._logger.critical(msg)

    def error(self, msg: str):
        return self._logger.error(msg)

    def warn(self, msg: str):
        return self._logger.warning(msg)

    def info(self, msg: str):
        return self._logger.info(msg)

    def debug(self, msg: str):
        return self._logger.debug(msg)
