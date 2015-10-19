from swift.common.swob import Request
from swift.common.utils import split_path
from Crypto.Cipher import AES
from Crypto import Random
import hashlib

AES_BLOCK = 32

def create_encrypt(raw, password):
    raw = _pad(raw)
    key = hashlib.sha256(password.encode()).digest()
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return iv + cipher.encrypt(raw)

def create_decrypt(enc, password):
    key = hashlib.sha256(password.encode()).digest()
    iv = enc[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    # return _unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')
    return _unpad(cipher.decrypt(enc[AES.block_size:]))

def _pad(s):
    return s + (AES_BLOCK - len(s) % AES_BLOCK) * chr(AES_BLOCK - len(s) % AES_BLOCK)

def _unpad(s):
    return s[:-ord(s[len(s)-1:])]


class EncryptMiddleware(object):
    """
    Encrypt middleware used for object Encryption

    """

    def __init__(self, app, conf):
        self.app = app
        self.conf = conf
        self.encrypt_suffix = conf.get('encrypt_suffix', '')
        self.password = conf.get('password', '')

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
                if not request.params.has_key('encrypt'):
                    response.body = response.body.replace(self.encrypt_suffix, '')
            return response(env, start_response)

        original_path_info = request.path_info
        request.path_info += self.encrypt_suffix
        if request.method == 'GET':
            if not request.params.has_key('encrypt'):
                # we need to decrypt
                response = request.get_response(self.app)
                if response.status_int == 404:
                    # it may not be encrypted, if admin added the encrypt filter after 
                    # some files have been uploaded
                    request.path_info = original_path_info
                    response = request.get_response(self.app)
                    return response(env, start_response)
                response.body = create_decrypt(response.body, self.password)
                return response(env, start_response)
       
        if request.method == 'PUT':
            if hasattr(request, 'body_file'):
                data = ""
                while True:
                    chunk = request.body_file.read()
                    if not chunk:
                        break
                    data += chunk
                encrypt_data = create_encrypt(data, self.password)
            else:
                encrypt_data = create_encrypt(request.body, self.password)
            if encrypt_data:
                request.body = encrypt_data

        response = request.get_response(self.app)
        return response(env, start_response)

def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)

    def encrypt_filter(app):
        return EncryptMiddleware(app, conf)
    return encrypt_filter

