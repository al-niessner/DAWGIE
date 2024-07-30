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
        self.assertFalse(dawgie.security.useClientVerification(),
                         'clear known serts')
        dawgie.security._certs.extend (['a','b','c'])
        dawgie.security._tls_initialize()
        self.assertFalse(dawgie.security.useClientVerification(),
                         'clear known serts')
        # FUTURE: when dawgie.security is updated, this should expect ValueError
        dawgie.security._tls_initialize(self.wdir)
        self.assertFalse(dawgie.security.useClientVerification(),
                         'clear known serts')
        with open (os.path.join (self.wdir, 'dawgie.public.pem'),'tw') as file:
            file.write ('bad cert')
        with self.assertRaises(OpenSSL.crypto.Error):
            dawgie.security._tls_initialize(self.wdir)
        self.assertFalse(dawgie.security.useClientVerification(),
                         'clear known serts')
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
        self.assertTrue (dawgie.security.useClientVerification(),
                         'find and load client cert')
        base = os.path.join (self.wdir, 'myself')
        with self.assertRaises(FileNotFoundError):
            dawgie.security._tls_initialize(self.wdir, base)
        self.assertTrue (dawgie.security.useClientVerification(),
                         'find and load client certs')
        self.assertFalse (dawgie.security.useTLS(), 'could not load')
        with open (os.path.join (self.wdir, 'myself.private'),'tw') as file:
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
        with self.assertRaises(OpenSSL.crypto.Error):
            dawgie.security._tls_initialize(self.wdir, base)
        self.assertTrue (dawgie.security.useClientVerification(),
                         'find and load client certs')
        self.assertFalse (dawgie.security.useTLS(), 'could not load')
        with open (os.path.join (self.wdir, 'myself.private'),'tw') as file:
            file.write ('''-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCsHUBbz4USAXfS
raguO9CXuwi81BOMUOw19QcSsqg5ISc7r2T9G0TMQ/OyUXE8JZlBLIH7xxchp+3K
MYjddzKYe3bInNcrzbAbc+sZ6Ab8Cf8Bil11cvcx9dJcwfJBI0ZrU6UZCTyGNjPK
TKq6ge0rCu2B9P323JKaXySlRWSAJeqjAoLfbVmL7/JkLuq02OuP+sUed/7aAss9
DqEInMN6lk0YnEM8lGYHu1N1nva0Q24o26KnEZwfbqBH5wZ7/J+cNMjvViJZcq68
o5b/2xA/IXvmQpYX86MXDS0cbB18A6Hhsjk3oylpDmprj/VJIs8YgW0c+E4YW/vL
eFTgVNXhAgMBAAECggEAKgZSaph3A3h8S2K/h9pvCj1O2txlkYNIybv0aCpbTOe9
bqNa4zo/SCjnXgjovyjnDLTTYCiyizM3qoEBzCGIpxauYDl7iGSGtY1OQFsZKX0/
WJ7yRvU1SmudW6y3fBQi453e2AgbUSH271Rc84E56aKXb33kbNxap3rHtdsFuQwi
fI+Y0gDDzRjNlkXPuY2X9ZSp+qWC9xsAL7sQX1a21nqzBPJeEe74ZOZ4rRPfE8nj
rgTakLkjtY3IZVvofxpyn7r6sVa5tETtw0+8TaVf1pK4sJzLCQJKxJPYw9G0B7Hq
HhBA1HRpiAKhhABJioiBDXtjvy+5qnGVYmVRbQksCQKBgQDX1uZ//pL7SGgTtq8K
V2HtLNp2eKSA1EDMlGI/rCTPz0PyvfdI/oXt1pMJpRge62pY0+s1TgW2qpcQiqbL
TqTIc3RUu+JR6pF++655rDFDr5tIB8p7tfHBlif4KoOuypuBO15n8HakBG3GrzcQ
2yMnr8WnYrXfy3+rPWJvOAD+xwKBgQDMI5XMRH7ETR6wI2oWUg2bTw4DNlQGw3Zu
eSOo5deNlThIww6k30y6fWPW9MT6BpW1UDH6Q9Z88kZEuO00L5FXddYj8y6GsswJ
Yv5Fhg/oE/qNRsjNd7YeL52cO79JtxpZJ65qdqsIkeY03AbEEY+9EhTMLno331F8
nST4Vmh+FwKBgBvZVpRdPIm/pe4lPCCRdcksaGOw3UjiGhpLawHcLEPD8nh3mliI
vq8ZaI9uBda3eVlMvqR6FLKlACjaOvswgoJ6ox/rvh/jrDI+Nxzr4s9g8SAyISYl
K7RWs4GJusPq0HW0O1Id7LDtAV0Jbol2POr5+v7F9cGSeD6YBQNkrnwxAoGAGrHE
kvOaCB11l97proWIVfjegjkGf+PrhsK8kQeNSmxq8cjgD1tL808WUTOs1m0qAo28
G1fnomskGTR9gEeAIAm+uPDB8sdKuyeAzKKdTeHe776D36p53DSpzZZai08wWNxB
iJaAAxzhF6R2Fgmd3EGTCqhBPzEqvLrn7LmP7H0CgYBmAgEHhHe+qLeTHsKDnRfd
i8bkpJfhU4/ntmFPIR0ALnBkiKV7OJkALyI8M+Fr8TciPhxlfDRBViLZu8l91PZE
Qi0F/Y1hN1mm2UjP/ib74fmyGfVs8YO9wrXLgByWGwZOWTyfw99x3h0w0QOhrLpA
M8M7jTBBKoKWY9y9yeplRA==
-----END PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
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
        with self.assertRaises(FileNotFoundError):
            dawgie.security._tls_initialize(self.wdir, base)
        self.assertTrue (dawgie.security.useClientVerification(),
                         'find and load client certs')
        self.assertFalse (dawgie.security.useTLS(), 'could not load')
        with open (os.path.join (self.wdir, 'myself.public'),'tw') as file:
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
        dawgie.security._tls_initialize(self.wdir, base)
        self.assertTrue (dawgie.security.useClientVerification(),
                         'find and load client certs')
        self.assertTrue (dawgie.security.useTLS(), 'could not load')
        return
    pass
