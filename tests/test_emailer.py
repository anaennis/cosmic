import os
import unittest
from unittest import mock

from src.emailer import build_message, email_settings_from_env, send_digest_email

SETTINGS = {'user': 'me@gmail.com', 'password': 'app-pass', 'to': 'me@stanford.edu',
            'host': 'smtp.gmail.com', 'port': 465}


class TestEmailSettings(unittest.TestCase):
    def test_reads_environment(self):
        env = {'EMAIL_USER': 'me@gmail.com', 'EMAIL_APP_PASSWORD': 'app-pass',
               'EMAIL_TO': 'me@stanford.edu'}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(email_settings_from_env(), SETTINGS)

    def test_custom_server(self):
        env = {'EMAIL_USER': 'u', 'EMAIL_APP_PASSWORD': 'p', 'EMAIL_TO': 't',
               'SMTP_HOST': 'smtp.example.com', 'SMTP_PORT': '2465'}
        with mock.patch.dict(os.environ, env, clear=True):
            settings = email_settings_from_env()
        self.assertEqual((settings['host'], settings['port']), ('smtp.example.com', 2465))

    def test_missing_settings_are_named(self):
        with mock.patch.dict(os.environ, {'EMAIL_USER': 'u'}, clear=True):
            with self.assertRaises(ValueError) as ctx:
                email_settings_from_env()
        self.assertIn('EMAIL_APP_PASSWORD', str(ctx.exception))
        self.assertIn('EMAIL_TO', str(ctx.exception))
        self.assertNotIn('EMAIL_USER', str(ctx.exception))


class TestMessage(unittest.TestCase):
    def test_has_text_and_html_parts(self):
        message = build_message('Subject', '<p>Hi</p>', 'Hi', 'a@x.com', 'b@x.com')
        self.assertEqual(message['Subject'], 'Subject')
        self.assertEqual(message['To'], 'b@x.com')
        self.assertEqual(message.get_body(('plain',)).get_content().strip(), 'Hi')
        self.assertEqual(message.get_body(('html',)).get_content().strip(), '<p>Hi</p>')

    def test_send_logs_in_and_sends(self):
        with mock.patch('smtplib.SMTP_SSL') as smtp:
            send_digest_email('Subject', '<p>Hi</p>', 'Hi', SETTINGS)
        smtp.assert_called_once_with('smtp.gmail.com', 465, timeout=30)
        server = smtp.return_value.__enter__.return_value
        server.login.assert_called_once_with('me@gmail.com', 'app-pass')
        sent = server.send_message.call_args[0][0]
        self.assertEqual(sent['From'], 'me@gmail.com')
        self.assertEqual(sent['To'], 'me@stanford.edu')


if __name__ == '__main__':
    unittest.main()
