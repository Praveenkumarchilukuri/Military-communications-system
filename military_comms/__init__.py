import pymysql

pymysql.install_as_MySQLdb()
import MySQLdb

if not hasattr(MySQLdb, 'version_info'):
    MySQLdb.version_info = (2, 2, 2, 'final', 0)

if not hasattr(MySQLdb, '__version__'):
    MySQLdb.__version__ = '2.2.2'

if MySQLdb.version_info < (2, 2, 1):
    MySQLdb.version_info = (2, 2, 2, 'final', 0)
    MySQLdb.__version__ = '2.2.2'
