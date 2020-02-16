from webdav.client import Client


class WebDAV(Client):
    def __init__(self, url: str, username: str = '', password: str = '', verify_ssl: bool = True):
        super().__init__({'webdav_hostname': url, 'webdav_login': username, 'webdav_password': password})
        self.default_options['SSL_VERIFYHOST'] = 1 if verify_ssl else 0
        self.default_options['SSL_VERIFYPEER'] = 1 if verify_ssl else 0
