from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from contextlib import contextmanager
import functools
import sqlite3


IntegrityError = sqlite3.IntegrityError


def atomic(f):
    @functools.wraps(f)
    def f_with_transactions(self, *args, **kwargs):
        self._connection.rollback()
        try:
            value = f(self, *args, **kwargs)
            self._connection.commit()
            return value
        except:
            self._connection.rollback()
            raise

    return f_with_transactions


SQL_CREATE_TABLE = '''\
create table if not exists uuid_name(
    scope text not null,
    name text,
    uuid text,
    primary key (scope, uuid),
    unique (scope, name)
);
'''

SQL_ADD = '''\
insert into uuid_name(name, uuid, scope)
              values (:name, :uuid, :scope)
'''

SQL_GET_UUID = '''\
select uuid
from uuid_name
where scope = :scope
  and name = :name
'''

SQL_GET_NAME = '''\
select name
from uuid_name
where scope = :scope
  and uuid = :uuid
'''

SQL_RENAME = '''\
update uuid_name
set name = :new_name
where scope = :scope
  and name = :old_name
'''


class UuidTranslator(object):

    def __init__(self, connection):
        self._connection = connection
        self._cursor = self._connection.cursor()
        try:
            self._cursor.executescript(SQL_CREATE_TABLE)
            self._connection.commit()
        except:
            self._connection.rollback()
            raise

    def _execute(self, sql, **kwargs):
        self._cursor.execute(sql, kwargs)
        return self._cursor.fetchall()

    def get_uuid(self, scope, name):
        try:
            (uuid,), = self._execute(SQL_GET_UUID, scope=scope, name=name)
            return uuid
        except ValueError:
            raise LookupError(dict(scope=scope, name=name))

    def get_name(self, scope, uuid):
        try:
            (name,), = self._execute(SQL_GET_NAME, scope=scope, uuid=uuid)
            return name
        except ValueError:
            raise LookupError(dict(scope=scope, uuid=uuid))

    def has_name(self, scope, name):
        return bool(self._execute(SQL_GET_UUID, scope=scope, name=name))

    @atomic
    def add(self, scope, uuid, name):
        self._execute(
            SQL_ADD,
            scope=scope, uuid=uuid, name=name,
        )

    @atomic
    def rename(self, scope, old_name, new_name):
        self._execute(
            SQL_RENAME,
            scope=scope,
            old_name=old_name, new_name=new_name,
        )


@contextmanager
def uuid_translator(database_path):
    connection = sqlite3.connect(database_path)
    connection.isolation_level = 'DEFERRED'
    try:
        yield UuidTranslator(connection)
    finally:
        connection.rollback()
        connection.close()
