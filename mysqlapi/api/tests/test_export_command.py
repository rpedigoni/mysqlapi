from unittest import TestCase
from django.conf import settings
from django.test.utils import override_settings

from mysqlapi.api.management.commands.export import Command

import mock
import subprocess


class ExportCommandTestCase(TestCase):
    def test_export(self):
        with mock.patch("subprocess.check_output") as check_output:
            with mock.patch("mysqlapi.api.management.commands.export.Command.send_data") as send_data:
                Command().handle_noargs()
                check_output.assert_called_with(
                    ["mysqldump", "-u", "root", "--quick", "--all-databases", "--compact"],
                    stderr=subprocess.STDOUT
                )

    def test_export_should_send_data(self):
        with mock.patch("subprocess.check_output") as check_output:
            check_output.return_value = "data"
            with mock.patch("mysqlapi.api.management.commands.export.Command.send_data") as send_data:
                Command().handle_noargs()
                send_data.assert_called_with("data")

    @override_settings(S3_ACCESS_KEY="access", S3_SECRET_KEY="secret")
    def test_send_data_should_get_keys_from_settings(self):
        access = settings.S3_ACCESS_KEY
        secret = settings.S3_SECRET_KEY
        with mock.patch("boto.s3.connection.S3Connection") as s3con:
            conn = mock.Mock()
            s3 = s3con.return_value
            s3.return_value = conn
            with mock.patch("boto.s3.key.Key") as key:
                Command().send_data("data")
                s3con.assert_called_with(access, secret)

    @override_settings(S3_BUCKET="bucket")
    def test_send_data_should_get_buckets_from_settings(self):
        bucket = settings.S3_BUCKET
        with mock.patch("boto.s3.connection.S3Connection") as s3con:
            conn = mock.Mock()
            s3 = s3con.return_value
            s3.return_value = conn
            with mock.patch("boto.s3.key.Key") as key:
                Command().send_data("data")
                s3.create_bucket.assert_called_with(bucket)

    def test_send_data(self):
        with mock.patch("boto.s3.connection.S3Connection") as s3con:
            conn = mock.Mock()
            s3 = s3con.return_value
            s3.return_value = conn
            with mock.patch("boto.s3.key.Key") as Key:
                key = Key.return_value
                Command().send_data("data")
                key.set_contents_from_string.assert_called_with("data")