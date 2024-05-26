import unittest
from argparse import Namespace
from unittest.mock import patch

from app.localization import setup_localization


class TestLocalization(unittest.TestCase):
    @patch("app.localization.argparse.ArgumentParser.parse_known_args")
    def test_setup_localization_returns_correct_languages(self, mock_args):
        # Mock the arguments returned from parse_known_args to simulate different languages
        mock_args.return_value = (Namespace(lang="en"), [])

        # Test defaults - should be English by default
        _, lang = setup_localization()
        self.assertEqual(lang, "en")

        # Change the mocked language to 'zh'
        mock_args.return_value = (Namespace(lang="zh"), [])
        _, lang = setup_localization()

        # Test if the returned language is 'zh'
        self.assertEqual(lang, "zh")

    @patch("app.localization.gettext.translation")
    def test_setup_localization_valid_directory(self, mock_translation):
        # Imagine this is your valid translation object with the gettext method
        valid_translation_object = type("valid_translation", (object,), {})()
        setattr(valid_translation_object, "gettext", lambda x: "translated text")

        # Mock the translation object to return our valid translation object
        mock_translation.return_value = valid_translation_object

        # Call setup_localization
        translation_function, _ = setup_localization()

        # Test if the translation returns expected translated text
        self.assertEqual(translation_function("input text"), "translated text")


if __name__ == "__main__":
    unittest.main()
