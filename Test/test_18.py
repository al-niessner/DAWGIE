'''

COPYRIGHT:
Copyright (c) 2015-2024, California Institute of Technology ("Caltech").
U.S. Government sponsorship acknowledged.

All rights reserved.

LICENSE:
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.

- Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

- Neither the name of Caltech nor its operating division, the Jet
Propulsion Laboratory, nor the names of its contributors may be used to
endorse or promote products derived from this software without specific prior
written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

NTR:
'''

import dawgie.security
import OpenSSL.crypto
import os
import shutil
import tempfile
import unittest

class Security(unittest.TestCase):
    '''check just the TLS client certificate lookups'''
    @classmethod
    def setUpClass(cls):
        cls.wdir = tempfile.mkdtemp()
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.wdir,True)

    def test_init(self):
        dawgie.security._tls_initialize()
        self.assertFalse(dawgie.security.useTLS(), 'clear known serts')
        dawgie.security._certs.extend (['a','b','c'])
        dawgie.security._tls_initialize()
        self.assertFalse(dawgie.security.useTLS(), 'clear known serts')
        # FUTURE: when dawgie.security is updated, this should expect ValueError
        dawgie.security._tls_initialize(self.wdir)
        self.assertFalse(dawgie.security.useTLS(), 'clear known serts')
        with open (os.path.join (self.wdir, 'dawgie.public.pem'),'tw') as file:
            file.write ('bad cert')
        with self.assertRaises(OpenSSL.crypto.Error):
            dawgie.security._tls_initialize(self.wdir)
        self.assertFalse(dawgie.security.useTLS(), 'clear known serts')
        with open (os.path.join (self.wdir, 'dawgie.public.pem'),'tw') as file:
            file.write ('''-----BEGIN CERTIFICATE-----
MIID7DCCAtSgAwIBAgIUB0JGjlKNuRBhs1ElGrhsobOa+AMwDQYJKoZIhvcNAQEL
BQAwTDELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAkNBMQswCQYDVQQHDAJMQTENMAsG
A1UECgwETm9uZTEUMBIGA1UEAwwLZXhhbXBsZS5jb20wHhcNMjQwNjE3MjI1NzA5
WhcNMjQwNzE3MjI1NzA5WjBMMQswCQYDVQQGEwJVUzELMAkGA1UECAwCQ0ExCzAJ
BgNVBAcMAkxBMQ0wCwYDVQQKDAROb25lMRQwEgYDVQQDDAtleGFtcGxlLmNvbTCC
ASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKwdQFvPhRIBd9KtqC470Je7
CLzUE4xQ7DX1BxKyqDkhJzuvZP0bRMxD87JRcTwlmUEsgfvHFyGn7coxiN13Mph7
dsic1yvNsBtz6xnoBvwJ/wGKXXVy9zH10lzB8kEjRmtTpRkJPIY2M8pMqrqB7SsK
7YH0/fbckppfJKVFZIAl6qMCgt9tWYvv8mQu6rTY64/6xR53/toCyz0OoQicw3qW
TRicQzyUZge7U3We9rRDbijboqcRnB9uoEfnBnv8n5w0yO9WIllyrryjlv/bED8h
e+ZClhfzoxcNLRxsHXwDoeGyOTejKWkOamuP9UkizxiBbRz4Thhb+8t4VOBU1eEC
AwEAAaOBxTCBwjBxBgNVHSMEajBooVCkTjBMMQswCQYDVQQGEwJVUzELMAkGA1UE
CAwCQ0ExCzAJBgNVBAcMAkxBMQ0wCwYDVQQKDAROb25lMRQwEgYDVQQDDAtleGFt
cGxlLmNvbYIUB0JGjlKNuRBhs1ElGrhsobOa+AMwCQYDVR0TBAIwADALBgNVHQ8E
BAMCBPAwFgYDVR0RBA8wDYILZXhhbXBsZS5jb20wHQYDVR0OBBYEFD5c+Y/S6R3o
/YZFk1ryaocGvurPMA0GCSqGSIb3DQEBCwUAA4IBAQA7eiGwmY9ofOOFXpACRKHc
uQBNALbz9eIA8RX8wZ3qwNJxFUoGQB5sxsJqHHuYnTwDVb4Ce2CYwyBFdlAxL2Vz
VOC39NCgAjZWOf3k3cUcttthbGIHNfdutqEwHxRCm7Aeoe+MKWRll6yKwXu+klne
l18iXAzutefQoEIOBI0V3/m3fgh5AIRqOlTiruFPnO6yLVLtg2GpQc2ZHMNhSWyg
P3pZlXKkWW0k5n3SG2+I4YIPrPHwxcSQ9fugdGrnC6Vk6lIvTImxe7ljYbnSsSVV
V/k0LmJRUq2Od3GDfotVRtx5uON2LLthI90HCHtTYudtn4VeVrWjiJuFgbSJNJNR
-----END CERTIFICATE-----
''')
        dawgie.security._tls_initialize(self.wdir)
        self.assertTrue (dawgie.security.useTLS(), 'find and load cert')
        return
    pass
