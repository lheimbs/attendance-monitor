"""Application entry point."""
import os
import re
from logging import Filter
from logging.config import dictConfig
from hashlib import sha512

from attendancecontrol import create_app


class RedactingFilter(Filter):
    def filter(self, record):
        # print(record.msg)
        # print(self.redact(record.msg))
        record.msg = self.redact(record.msg)
        if isinstance(record.args, dict):
            for k in record.args.keys():
                record.args[k] = self.redact(record.args[k])
        else:
            record.args = tuple(self.redact(arg) for arg in record.args)
        return True

    def replace_pwd(self, match_object):
        # print(match_object.group("pwd"))
        if match_object.group("pwd"):
            hashed_pwd = sha512(match_object.group("pwd").encode()).hexdigest()
            return match_object[0].replace(match_object.group('pwd'), hashed_pwd)
        return match_object[0]

    def redact(self, msg):
        msg = str(msg)
        return re.sub(r'(?:(\w+):\/\/(.*?):)(?P<pwd>.*?)(?:\@(.*?):(.*?)\/(\w+))', self.replace_pwd, msg)


dictConfig({
    'version': 1,
    'filters': {
        'myfilter': {
            '()': RedactingFilter,
        }
    },
    'formatters': {'default': {
        'format': 'File "%(pathname)-75s", line %(lineno)-3d, in %(funcName)-20s: %(levelname)-8s : %(message)s',
        # 'funcName: %(funcName)s line: %(lineno)d path: %(pathname)s filename: %(filename)s module: %(module)15s -
        # %(levelname)-8s : %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default',
        'filters': ['myfilter']
    }},
    'root': {
        'level': os.environ.get('LOG_LEVEL', 'WARNING'),
        'handlers': ['wsgi']
    }
})


app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
