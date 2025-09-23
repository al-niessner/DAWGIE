# to test postgres:
#   docker pull postgres:latest
#   docker run --detach --env POSTGRES_PASSWORD=password --env POSTGRES_USER=tester --env POSTGRES_HOST_AUTH_METHOD=trust --name postgres --publish 5432:5432 --rm  postgres:latest
#   docker exec -i postgres createdb -U tester testspace
#   python dup.py <output of first run to not load each time>
#
# notes:
#   takes about 5 minutes to load the database
#   once loaded it can simply be re-used (no reason to dump and start again)

import sys
import test_13
import unittest

if len(sys.argv) > 1:
    test_13.Post.setUpClass(sys.argv[1])
else:
    test_13.Post.setUpClass()
    print(test_13.Post.root)

test_13.Post().test_remove()

# normally the temp directory would be cleaned up here
# test_13.Post.tearDownClass()

