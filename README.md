swift-compress-encrypt-middleware
=======================

Code for OpenStack Swift middleware. When an object is uploaded, we compress and then encrypt the object in the background. This can save space in the backend, and secure the data.

This compression and encryption is transparent to end users.

Install:

Install the middleware first:
    pip install -r requirements.txt
    python setup.py install

Compress middleware and encrypt middleware can be used separately or combined.

Insert the middleware in your Swift proxy server configuration:

For example, put the compress and/or encrypt before the app proxy-server
    pipeline = catch_errors gatekeeper healthcheck proxy-logging cache bulk tempurl ratelimit crossdomain container_sync tempauth staticweb container-quotas account-quotas slo dlo versioned_writes proxy-logging compress encrypt proxy-server

Then add the filters here:

    [filter:encrypt]
    use = egg:myswift#encrypt
    encrypt_suffix = .encryptF4ASqYLMzx
    password = password123456

    [filter:compress]
    use = egg:myswift#compress
    compress_suffix = .compressF4ASqYLMzx

Make the encrypt_suffix and compress_suffix unique by adding random characters. This is an identifier indicating the object type(compressed or encrypted).
