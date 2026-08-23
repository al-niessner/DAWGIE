'''

COPYRIGHT:
Copyright (c) 2015-2026, California Institute of Technology ("Caltech").
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
        shutil.rmtree(cls.wdir, True)

    def test_init(self):
        dawgie.security._tls_initialize()
        self.assertFalse(
            dawgie.security.use_client_verification(), 'clear known certs'
        )
        dawgie.security._guests.update({'path': '', 'certs': ['a', 'b', 'c']})
        dawgie.security._tls_initialize()
        self.assertFalse(
            dawgie.security.use_client_verification(), 'clear known certs'
        )
        # FUTURE: when dawgie.security is updated, this should expect ValueError
        dawgie.security._tls_initialize(self.wdir)
        self.assertFalse(
            dawgie.security.use_client_verification(), 'clear known certs'
        )
        with open(os.path.join(self.wdir, 'signed.public.pem.1'), 'tw') as file:
            file.write('bad cert')
        dawgie.security._tls_initialize(self.wdir)
        self.assertFalse(  # because there is no CA no clients are read
            dawgie.security.use_client_verification(), 'clear known certs'
        )
        # add CA here then it should fail
        '''
$ openssl req -x509 -new -nodes -newkey rsa:4096   -keyout test-ca.key -out test-ca.crt    -days 36500         -subj "/CN=DAWGIE Unit Testing"         -addext "basicConstraints=critical,CA:TRUE,pathlen:0"         -addext "keyUsage=critical,keyCertSign,cRLSign"         -addext "extendedKeyUsage=clientAuth"         -addext "nameConstraints=critical,permitted;URI:dawgie.local"
$ cat test-ca.key test-ca.crt > test-ca.pem
        '''
        auth = os.path.join(self.wdir, 'ca.pem')
        with open(auth, 'tw') as file:
            file.write('''
-----BEGIN PRIVATE KEY-----
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
wRmOU+Gg4ZqBqvyleZDeiEZjDncKrQ==
-----END PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
MIIFaTCCA1GgAwIBAgIUcASy6z0FeJta7z1u4+OA4YzY+/gwDQYJKoZIhvcNAQEL
BQAwHjEcMBoGA1UEAwwTREFXR0lFIFVuaXQgVGVzdGluZzAgFw0yNjA4MTgyMDQ5
NTBaGA8yMTI2MDcyNTIwNDk1MFowHjEcMBoGA1UEAwwTREFXR0lFIFVuaXQgVGVz
dGluZzCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAOStqrHqn0IjMvAY
4Y5lGOB7NdcT9Mii381qyOUlT+JzFIScUCv7CX4Btx5PXbtSKzq0ade6Xn/LFIjH
5liYmpcsiZ1Pu5afIMmAsbnw063EonBPsR1kWJ1bggYNkYLHilW+IMtn4YfE/6nZ
mcSH+6qw8FGuz4sg5JKqv0A4RqaVtDX4opbCLcYgddfvv8953YnSAy4UmbGarY+x
I/gDnOSaG6ny/svJjqYOW2+ZHWO2P4I/Ec7ReYvxUO/Tc6Ln5ZLI3aVQWqeUIMhb
OrTZpu23TUbjjHZhfd9EwQe5IFMpZ40VCeIwTKc+K2JGuzHFZo2FmHrKUSisXgLS
wjsnxKdr4AVg0hY/AEd5Izb9sNbZqCkc7Xzjl5mGfuY3rGHzu8/lRBf7zMQguyuW
KcqzdC4ZeXrIsIpLtY+C58gpIR2IeeTeDu+Rgjo2iVNGbnYLNvXca2up+Cn/CQh4
Cq4j4nN+FkbzN0N4y5tQKNtcAhWYTUWdxytT5YowdWeWBjlrUbdj6+fb5a05w2nv
43KUK3UkyDa31IXrZDQwHaavAH0D7QxvtU1B0gKRz6Moms+pDRDC19qOdg/aXDvG
4rkTXrm7orG9BBfHbMl1xZ99RiSUhwhNgq2XzgOdXBCQAtE/EwyKLQRem1a31RWp
fzsAj4+bM7IejSSQ4lbVT3EXpn7RAgMBAAGjgZwwgZkwHQYDVR0OBBYEFOMFSH9l
xqoBVwJHpr5AZxBPBCLSMB8GA1UdIwQYMBaAFOMFSH9lxqoBVwJHpr5AZxBPBCLS
MBIGA1UdEwEB/wQIMAYBAf8CAQAwDgYDVR0PAQH/BAQDAgEGMBMGA1UdJQQMMAoG
CCsGAQUFBwMCMB4GA1UdHgEB/wQUMBKgEDAOhgxkYXdnaWUubG9jYWwwDQYJKoZI
hvcNAQELBQADggIBADpECFoLu2vCKJdI3YtWeFkdR+FzYXIzmplum4YJjOSiHEi4
SED8jju0PC2wjfLorMwm4ilr2o76QuJDWwDJhHJYZ6lW/65nc5r82pANHILm32md
6kMefVq/zL7s4rpkrqgp/D7f7q7sYLSIbNK6LniHdGQ+hHZMzaj83zk07aWnE1xR
a1M7xXA604OTDrghJ4UxqNyY7zM2qHUudhLyGuAUXqvpKhMwrNhV/CZIP8d8UV/2
3foYPY1LHFibymNHBj+WqzWV/XZrO6n8qaxJTsx91/G/wAFxRT5wLuQFxhpGRTI8
egoS+5Nl0ZBZK5tMHhkTMM1az83PO7i8Wj4zpAl1Va+qqT02fJPrdEgzRHppxGW4
3jYa/i0B1k0SGWfYHbyYSDz/bgVoHA4DqA8Q7oztCJO+9hfggaax0MNwVzl9+/4A
bh+0UAX1J6OMNN5AQsxPy/QRk9OKmYt/VvQFM0tLAis2elztTq7LsY/HNfZda8q8
9TxiLDXpKzxg4r+Ownyj+mMyaz+oUFJqyBdgdgAaOLawxlF8phX1HxIAy0ZLnAIa
o6TBub8WW3Jh8Rb8Qb7lXq/2jQhdbvk1ql4veV9H5ybf3DSXxafESplW3lsrJbTq
7rKqdlCPwd2K1a/GQdJoP/CiWMbXOgGHe5N32Lkz7rToRRBoOj4JEGRY03Dt
-----END CERTIFICATE-----
''')
            os.chmod(auth, 0o600)
        with self.assertRaises(OpenSSL.crypto.Error):  # because cert is garbage
            dawgie.security._tls_initialize(self.wdir, myauth=auth)
        self.assertFalse(
            dawgie.security.use_client_verification(), 'clear known certs'
        )
        # add a cert that is not signed
        with open(os.path.join(self.wdir, 'signed.public.pem.1'), 'tw') as file:
            file.write('''-----BEGIN CERTIFICATE-----
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
        # should fail because this is not signed by CA
        dawgie.security._tls_initialize(self.wdir, myauth=auth)
        self.assertFalse(  # because cert is not signed by CA
            dawgie.security.use_client_verification(), 'clear known certs'
        )
        '''
$ openssl req -new -nodes -newkey rsa:2048             -keyout test.key -out test.csr             -subj "/CN=test"
$ cat > v3.ext <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=clientAuth
subjectAltName=URI:https://dawgie.local/user/test
EOF
$ openssl x509 -req -in test.csr             -CA test-ca.crt -CAkey test-ca.key -CAcreateserial             -out test.crt -sha256 -extfile v3.ext -days 36500   $ openssl verify -CAfile test-ca.pem test.crt
test.crt: OK
     '''
        with open(os.path.join(self.wdir, 'signed.public.pem.2'), 'tw') as file:
            file.write('''
-----BEGIN CERTIFICATE-----
MIIEXzCCAkegAwIBAgIUM/OBx8IOV/DfFrEFzAw0Geta7I0wDQYJKoZIhvcNAQEL
BQAwHjEcMBoGA1UEAwwTREFXR0lFIFVuaXQgVGVzdGluZzAgFw0yNjA4MTgyMDUz
MzhaGA8yMTI2MDcyNTIwNTMzOFowDzENMAsGA1UEAwwEdGVzdDCCASIwDQYJKoZI
hvcNAQEBBQADggEPADCCAQoCggEBALI8G+NAlFvVg8LktO9CLhW6L+nT6OzOloAD
uUhGzD6lgzVHlpsLLWEbkbInIa51rBTAysjqkhxqf0GrsFORsXoznAW/E6fP4HQY
gC2+CEMKM4b8ecDlKpkn0BgVVul8NqUXE6BZUkNCMmV5WBB2qAzKcuaIVz1/+Yu6
XoZG6iSbw/48G7ZnK3/QbHultGR2R0lAVvCjxjyHdTtJ7viwDbBV6w3tN0uZrn87
m27G7zoHg3DIwGPbhGwCixRpax1dT6iGuiHH5OogobF+L60ovLsEQy/N9BFxuWT9
Z5xXhe85OD3JMCK2408GRJxyJJ82KX//YBeLP8B48IQf218ZNv8CAwEAAaOBoTCB
njAfBgNVHSMEGDAWgBTjBUh/ZcaqAVcCR6a+QGcQTwQi0jAMBgNVHRMBAf8EAjAA
MA4GA1UdDwEB/wQEAwIFoDATBgNVHSUEDDAKBggrBgEFBQcDAjApBgNVHREEIjAg
hh5odHRwczovL2Rhd2dpZS5sb2NhbC91c2VyL3Rlc3QwHQYDVR0OBBYEFFLBmkFz
5guEFaE5t/pFw/CIISgoMA0GCSqGSIb3DQEBCwUAA4ICAQCl4kXOzkQzbadPnGpO
otq5ei4EtF7BUqRgWftKi1Ol9r06+tKUZiOusNtoKrAKv5YejGHM1p3Ld3JlWNeg
Ig75L0vJ9keUtqD2Rx0+SugfGK4VK/gwSbjRbA6adjACWDBhQjdtjAM5aHg2fkqD
Ak6jMeQnflG4q6Ss0j9nn66AWYQH3wPaOJ+X3/7oeqT0Xrr5PPZgxmGAvF17pFGe
v2o/U0QSAyJ2i848KzH2BGOGurKAWsLwJj55lvEYngX47kKDfksH9m3rfzup5vPi
yC9xetc75CLvJfPQuZwzC4x2CYJuCHjRZgv1R8eWsHALjIQ3uOMqTHCCRl53bbXy
Tu32GoQb6oQfFWJ5DNI2gL8j3Q+K9l1LSEN3qcvbiDXMVLQI3pokGRFqBqodAtwt
bDy9JPIhKmC7JkxYRdYkoejOMQIDOLfAnULgyf/4xXJRachRXM8OY0rwLlis9RdD
IqpwMupGZYQbmSf8GNVss/qkktle8wJ6jOyQPDfDxwzCh6zPgbu0wwMoK85DS5pJ
f7qgg5o/sGXXeW4/WzoP2rSfkSozzsCbfHS/zGl3jb7fUMP1E57nvy7k6sDEAnpf
vAMQ03c3Z4am3wHNvwVGS6VE7NJtgzl4s2odLmbG7dmPGVeNtFlhT6TCo1PMsNat
9IC3GmuwzXXaivjnDyzVQmjs4w==
-----END CERTIFICATE-----
''')
        dawgie.security._tls_initialize(self.wdir, myauth=auth)
        self.assertTrue(
            dawgie.security.use_client_verification(),
            'find and load client cert',
        )
        base = os.path.join(self.wdir, 'myself.pem')
        with self.assertRaises(FileNotFoundError):
            dawgie.security._tls_initialize(
                self.wdir, auth, 'example.com', base
            )
        self.assertFalse(
            dawgie.security.use_client_verification(),
            'find and load client certs',
        )
        self.assertFalse(dawgie.security.use_tls(), 'could not load')
        with open(base, 'tw') as file:
            file.write('''-----BEGIN CERTIFICATE-----
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
            dawgie.security._tls_initialize(
                self.wdir, auth, 'example.com', base
            )
        self.assertFalse(
            dawgie.security.use_client_verification(),
            'find and load client certs',
        )
        self.assertFalse(dawgie.security.use_tls(), 'could not load')
        with open(base, 'tw') as file:
            file.write('''-----BEGIN PRIVATE KEY-----
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
        dawgie.security._tls_initialize(self.wdir, auth, 'example.com', base)
        self.assertTrue(
            dawgie.security.use_client_verification(),
            'find and load client certs',
        )
        self.assertTrue(dawgie.security.use_tls(), 'could not load')
        return
