# -*- coding: utf-8 -*-
import os

from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import simplejson
from mocker import Mocker

from mysqlapi.api.models import DatabaseManager
from mysqlapi.api.database import Connection
from mysqlapi.api.views import _get_service_host, export, create_user, create_database, drop_user, drop_database, healthcheck


class CreateDatabaseViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = Connection(hostname="localhost", username="root")
        cls.conn.open()
        cls.cursor = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_create_database_should_returns_500_when_name_is_missing(self):
        request = RequestFactory().post("/", {})
        response = create_database(request)
        self.assertEqual(500, response.status_code)
        self.assertEqual("App name is missing", response.content)

    def test_create_database_should_returns_500_when_name_is_blank(self):
        request = RequestFactory().post("/", {"name": ""})
        response = create_database(request)
        self.assertEqual(500, response.status_code)
        self.assertEqual("App name is empty", response.content)

    def test_create_database_should_returns_500_and_error_msg_in_body(self):
        db = DatabaseManager("ciclops")
        db.create_database()
        request = RequestFactory().post("/", {"name": "ciclops"})
        response = create_database(request)
        self.assertEqual(500, response.status_code)
        self.assertEqual("Can't create database 'ciclops'; database exists", response.content)
        db.drop_database()

    def test_create_database_should_returns_405_when_method_is_not_post(self):
        request = RequestFactory().get("/")
        response = create_database(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().put("/")
        response = create_database(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().delete("/")
        response = create_database(request)
        self.assertEqual(405, response.status_code)

    def test_create_database(self):
        request = RequestFactory().post("/", {"name": "ciclops"})
        response = create_database(request)
        self.assertEqual(201, response.status_code)
        content = simplejson.loads(response.content)
        expected = {
            u"MYSQL_DATABASE_NAME": u"ciclops",
            u"MYSQL_HOST": u"localhost",
            u"MYSQL_PORT": u"3306",
        }
        self.assertDictEqual(expected, content)

        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'ciclops'")
        row = self.cursor.fetchone()
        self.assertEqual("ciclops", row[0])

        db = DatabaseManager("ciclops")
        db.drop_database()

    def test_create_database_returns_the_host_from_environment_variable(self):
        os.environ["MYSQLAPI_DATABASE_HOST"] = "10.0.1.100"
        request = RequestFactory().post("/", {"name": "plains_of_dawn"})
        response = create_database(request)
        self.assertEqual(201, response.status_code)
        content = simplejson.loads(response.content)
        expected = {
            u"MYSQL_DATABASE_NAME": u"plains_of_dawn",
            u"MYSQL_HOST": u"10.0.1.100",
            u"MYSQL_PORT": u"3306",
        }
        self.assertEqual(expected, content)
        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'plains_of_dawn'")
        row = self.cursor.fetchone()
        self.assertEqual("plains_of_dawn", row[0])
        db = DatabaseManager("plains_of_dawn")
        db.drop_database()

    def test_create_database_in_a_custom_service_host(self):
        request = RequestFactory().post("/", {"name": "ciclops", "service_host": "127.0.0.1"})
        response = create_database(request)
        self.assertEqual(201, response.status_code)
        content = simplejson.loads(response.content)
        expected = {
            u"MYSQL_DATABASE_NAME": u"ciclops",
            u"MYSQL_HOST": u"127.0.0.1",
            u"MYSQL_PORT": u"3306",
        }
        self.assertDictEqual(expected, content)

        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'ciclops'")
        row = self.cursor.fetchone()
        self.assertEqual("ciclops", row[0])

        db = DatabaseManager("ciclops")
        db.drop_database()


class CreateUserViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = Connection(hostname="localhost", username="root")
        cls.conn.open()
        cls.cursor = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_create_user_should_returns_500_when_hostname_is_missing(self):
        request = RequestFactory().post("/", {})
        response = create_user(request, "database")
        self.assertEqual(500, response.status_code)
        self.assertEqual("Hostname is missing", response.content)

    def test_create_user_should_returns_500_when_hostname_name_is_blank(self):
        request = RequestFactory().post("/", {"hostname": ""})
        response = create_user(request, "database")
        self.assertEqual(500, response.status_code)
        self.assertEqual("Hostname is empty", response.content)

    def test_create_user_should_returns_405_when_method_is_not_post(self):
        request = RequestFactory().get("/")
        response = create_user(request, "name")
        self.assertEqual(405, response.status_code)

        request = RequestFactory().put("/")
        response = create_user(request, "name")
        self.assertEqual(405, response.status_code)

        request = RequestFactory().delete("/")
        response = create_user(request, "name")
        self.assertEqual(405, response.status_code)

    def test_create_user(self):
        request = RequestFactory().post("/", {"hostname": "192.168.1.1"})
        response = create_user(request, "ciclops")
        self.assertEqual(201, response.status_code)
        content = simplejson.loads(response.content)
        expected = {
            u"MYSQL_USER": u"ciclops",
            u"MYSQL_PASSWORD": content["MYSQL_PASSWORD"],
        }
        self.assertDictEqual(expected, content)

        self.cursor.execute("select User, Host FROM mysql.user WHERE User='ciclops' AND Host='192.168.1.1'")
        row = self.cursor.fetchone()
        self.assertEqual("ciclops", row[0])
        self.assertEqual("192.168.1.1", row[1])

        db = DatabaseManager("ciclops")
        db.drop_user("ciclops", "192.168.1.1")

    def test_create_user_in_a_custom_service_host(self):
        request = RequestFactory().post("/", {"hostname": "192.168.1.1", "service_host": "127.0.0.1"})
        response = create_user(request, "ciclops")
        self.assertEqual(201, response.status_code)
        content = simplejson.loads(response.content)
        expected = {
            u"MYSQL_USER": u"ciclops",
            u"MYSQL_PASSWORD": content["MYSQL_PASSWORD"],
        }
        self.assertDictEqual(expected, content)

        self.cursor.execute("select User, Host FROM mysql.user WHERE User='ciclops' AND Host='192.168.1.1'")
        row = self.cursor.fetchone()
        self.assertEqual("ciclops", row[0])
        self.assertEqual("192.168.1.1", row[1])

        db = DatabaseManager("ciclops")
        db.drop_user("ciclops", "192.168.1.1")


class ExportViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = Connection(hostname="localhost", username="root")
        cls.conn.open()
        cls.cursor = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_export_from_a_custom_service_host(self):
        db = DatabaseManager("magneto", host="127.0.0.1")
        db.create_database()
        db.create_user("magneto", "localhost")
        self.cursor.execute("create table magneto.foo ( test varchar(255) );")
        expected = """/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `foo` (
  `test` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
"""
        request = RequestFactory().get("/", {"service_host": "127.0.0.1"})
        result = export(request, "magneto")
        self.assertEqual(200, result.status_code)
        self.assertEqual(expected, result.content.replace("InnoDB", "MyISAM"))
        db.drop_database()
        db.drop_user("magneto", "localhost")

    def test_export(self):
        db = DatabaseManager("magneto")
        db.create_database()
        db.create_user("magneto", "localhost")
        self.cursor.execute("create table magneto.foo ( test varchar(255) );")
        expected = """/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `foo` (
  `test` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
"""
        request = RequestFactory().get("/")
        result = export(request, "magneto")
        self.assertEqual(200, result.status_code)
        self.assertEqual(expected, result.content.replace("InnoDB", "MyISAM"))
        db.drop_database()
        db.drop_user("magneto", "localhost")

    def test_export_should_returns_500_when_database_does_not_exist(self):
        request = RequestFactory().get("/", {})
        response = export(request, "doesnotexists")
        self.assertEqual(500, response.status_code)
        self.assertEqual("Unknown database 'doesnotexists' when selecting the database", response.content)

    def test_export_should_returns_405_when_method_is_not_get(self):
        request = RequestFactory().post("/")
        response = export(request, "xavier")
        self.assertEqual(405, response.status_code)

        request = RequestFactory().put("/")
        response = export(request, "xavier")
        self.assertEqual(405, response.status_code)

        request = RequestFactory().delete("/")
        response = export(request, "xavier")
        self.assertEqual(405, response.status_code)


class DropUserViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = Connection(hostname="localhost", username="root")
        cls.conn.open()
        cls.cursor = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_drop_should_returns_500_and_error_msg_in_body(self):
        request = RequestFactory().delete("/")
        response = drop_user(request, "doesnotexists", "hostname")
        self.assertEqual(500, response.status_code)
        self.assertEqual("Operation DROP USER failed for 'doesnotexists'@'hostname'", response.content)

    def test_drop_should_returns_405_when_method_is_not_delete(self):
        request = RequestFactory().get("/")
        response = drop_user(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().put("/")
        response = drop_user(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().post("/")
        response = drop_user(request)
        self.assertEqual(405, response.status_code)

    def test_drop_user(self):
        db = DatabaseManager("ciclops")
        db.create_user("ciclops", "localhost")

        request = RequestFactory().delete("/ciclops")
        response = drop_user(request, "ciclops", "localhost")
        self.assertEqual(200, response.status_code)

        self.cursor.execute("select User, Host FROM mysql.user WHERE User='ciclops' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertFalse(row)

    def test_drop_user_fom_custom_service_host(self):
        db = DatabaseManager("ciclops", "127.0.0.1")
        db.create_user("ciclops", "localhost")

        request = RequestFactory().delete("/ciclops", {"service_host": "127.0.0.1"})
        response = drop_user(request, "ciclops", "localhost")
        self.assertEqual(200, response.status_code)

        self.cursor.execute("select User, Host FROM mysql.user WHERE User='ciclops' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertFalse(row)


class DropDatabaseViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = Connection(hostname="localhost", username="root")
        cls.conn.open()
        cls.cursor = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_drop_should_returns_500_and_error_msg_in_body(self):
        request = RequestFactory().delete("/")
        response = drop_database(request, "doesnotexists")
        self.assertEqual(500, response.status_code)
        self.assertEqual("Can't drop database 'doesnotexists'; database doesn't exist", response.content)

    def test_drop_should_returns_405_when_method_is_not_delete(self):
        request = RequestFactory().get("/")
        response = drop_database(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().put("/")
        response = drop_database(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().post("/")
        response = drop_database(request)
        self.assertEqual(405, response.status_code)

    def test_drop(self):
        db = DatabaseManager("ciclops")
        db.create_database()

        request = RequestFactory().delete("/ciclops")
        response = drop_database(request, "ciclops")
        self.assertEqual(200, response.status_code)

        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'ciclops'")
        row = self.cursor.fetchone()
        self.assertFalse(row)

    def test_drop_from_a_custom_service_host(self):
        db = DatabaseManager("ciclops", "127.0.0.1")
        db.create_database()

        request = RequestFactory().delete("/ciclops", {"service_host": "127.0.0.1"})
        response = drop_database(request, "ciclops")
        self.assertEqual(200, response.status_code)

        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'ciclops'")
        row = self.cursor.fetchone()
        self.assertFalse(row)


class DatabaseTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = Connection(hostname="localhost", username="root")
        cls.conn.open()
        cls.cursor = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_create_database_with_custom_hostname(self):
        db = DatabaseManager("newdatabase", host="127.0.0.1")
        db.create_database()
        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'newdatabase'")
        row = self.cursor.fetchone()
        self.assertEqual("newdatabase", row[0])
        db.drop_database()

    def test_create(self):
        db = DatabaseManager("newdatabase")
        db.create_database()
        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'newdatabase'")
        row = self.cursor.fetchone()
        self.assertEqual("newdatabase", row[0])
        db.drop_database()

    def test_drop(self):
        db = DatabaseManager("otherdatabase")
        db.create_database()
        db.drop_database()
        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'otherdatabase'")
        row = self.cursor.fetchone()
        self.assertFalse(row)

    def test_create_user(self):
        db = DatabaseManager("wolverine")
        db.create_user("wolverine", "localhost")
        self.cursor.execute("select User, Host FROM mysql.user WHERE User='wolverine' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertEqual("wolverine", row[0])
        self.assertEqual("localhost", row[1])
        db.drop_user("wolverine", "localhost")

    def test_create_user_should_generate_an_username_when_username_length_is_greater_than_16(self):
        db = DatabaseManager("usernamegreaterthan16")
        username, password = db.create_user("usernamegreaterthan16", "localhost")
        self.cursor.execute("select User, Host FROM mysql.user WHERE User like 'usernamegrea%' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertEqual("usernamegrea", row[0][:12])
        db = DatabaseManager(row[0])
        db.drop_user(username, "localhost")

    def test_drop_user(self):
        db = DatabaseManager("magneto")
        db.create_user("magneto", "localhost")
        db.drop_user("magneto", "localhost")
        self.cursor.execute("select User, Host FROM mysql.user WHERE User='wolverine' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertFalse(row)

    def test_export(self):
        db = DatabaseManager("magneto")
        db.create_database()
        db.create_user("magneto", "localhost")
        self.cursor.execute("create table magneto.foo ( test varchar(255) );")
        expected = """/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `foo` (
  `test` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
"""
        result = db.export()
        self.assertEqual(expected, result.replace("InnoDB", "MyISAM"))
        db.drop_database()
        db.drop_user("magneto", "localhost")

    def test_is_up_return_True_if_everything_is_ok_with_the_connection(self):
        db = DatabaseManager("wolverine")
        self.assertTrue(db.is_up())

    def test_is_up_return_False_something_is_not_ok_with_the_connection(self):
        db = DatabaseManager("wolverine", host="unknownhost.absolute.impossibru.moc")
        self.assertFalse(db.is_up())

class DatabaseConnectionTestCase(TestCase):

    def test_connection_should_return_a_connection(self):
        conn = Connection(hostname="localhost", username="root")
        conn.open()
        self.assertTrue(conn._connection)
        conn.close()

    def test_should_return_cursor(self):
        conn = Connection(hostname="localhost", username="root")
        conn.open()
        self.assertTrue(conn.cursor())
        conn.close()


class GetServiceHostTestCase(TestCase):

    def test_get_service_host_returns_localhost_if_the_key_is_not_present(self):
        self.assertEqual("localhost", _get_service_host({}))

    def test_get_service_host_returns_the_value_of_service_host_key_if_present(self):
        self.assertEqual("service.net", _get_service_host({"service_host": "service.net"}))

    def test_get_service_host_returns_localhost_if_the_key_is_an_empty_string(self):
        self.assertEqual("localhost", _get_service_host({"service_host": ""}))


class HealthcheckTestCase(TestCase):

    def test_healthcheck_returns_204_if_the_mysql_server_is_on(self):
        mocker = Mocker()
        obj = mocker.replace("mysqlapi.api.models.DatabaseManager.is_up")
        obj()
        mocker.result(True)
        mocker.replay()
        request = RequestFactory().get("/resources/g8mysql/status/")
        response = healthcheck(request, "g8mysql")
        self.assertEqual(204, response.status_code)
        mocker.verify()

    def test_healthcheck_returns_500_if_the_mysql_server_is_off(self):
        mocker = Mocker()
        obj = mocker.replace("mysqlapi.api.models.DatabaseManager.is_up")
        obj()
        mocker.result(False)
        mocker.replay()
        request = RequestFactory().get("/resources/g8mysql/status/")
        response = healthcheck(request, "g8mysql")
        self.assertEqual(500, response.status_code)
        mocker.verify()
