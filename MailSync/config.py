import inspect
import os
from configparser import ConfigParser


class Config(ConfigParser):
    def __init__(self, env_key: str = 'MAILSYNC'):
        super(Config, self).__init__()
        env_key = env_key.rstrip('__') + '__'
        for item in [(x.replace(env_key, ''), y) for x, y in os.environ.items() if x.startswith(env_key)]:
            item, value = item
            section, option = item.split('__')
            section = section.lower()
            option = option.lower()
            if section not in self.sections():
                self.add_section(section)
            self.set(section, option, value)

    def gen_conf_dict(self, section: str, obj=None):
        retr = {}
        section = section.lower()
        if obj is not None:
            obj = [x for x in inspect.getfullargspec(obj).args if x != 'self']
        if section in self.sections():
            options = self.options(section)
            if obj is not None:
                options = [x for x in options if x in obj]
            for option in options:
                option = option.lower()
                try:
                    retr.update({option: self.getint(section, option)})
                except:
                    try:
                        retr.update({option: self.getboolean(section, option)})
                    except:
                        retr.update({option: self.get(section, option)})

        return retr
