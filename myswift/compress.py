from swift.common.swob import Request
from swift.common.utils import split_path
import zlib
import hashlib


def create_compress(data):
    return zlib.compress(data)

def create_uncompress(data):
    return zlib.decompress(data)

class CompressMiddleware(object):
    """
    Compress middleware used for object compression

    """

    def __init__(self, app, conf):
        self.app = app
        self.conf = conf
        self.compress_suffix = conf.get('compress_suffix', '')

    def __call__(self, env, start_response):
        request = Request(env)
        try:
            (version, account, container, objname) = split_path(request.path_info, 1, 4, True)
        except ValueError:
            response = request.get_response(self.app)
            return response(env, start_response)
        if not objname:
            response = request.get_response(self.app)
            if container:
                if not request.params.has_key('compress'):
                    response.body = response.body.replace(self.compress_suffix, '')
            return response(env, start_response)

        original_path_info = request.path_info
        request.path_info += self.compress_suffix
        if request.method == 'GET':
            if not request.params.has_key('compress'):
                # we need to decompress
                response = request.get_response(self.app)

                if response.status_int == 404:
                    # it may not be compressed, if admin added the compress filter after 
                    # some files have been uploaded
                    request.path_info = original_path_info
                    response = request.get_response(self.app)
                    return response(env, start_response)
                uncompressed_data = create_uncompress(response.body)
                response.body = uncompressed_data
                return response(env, start_response)
       
        if request.method == 'PUT':
            if hasattr(request, 'body_file'):
                data = ""
                while True:
                    chunk = request.body_file.read()
                    if not chunk:
                        break
                    data += chunk
                request.body = data
                compress_data = create_compress(data)
            else:
                compress_data = create_compress(request.body)
            if compress_data:
                request.body = compress_data

        response = request.get_response(self.app)
        return response(env, start_response)

def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)

    def compress_filter(app):
        return CompressMiddleware(app, conf)
    return compress_filter

