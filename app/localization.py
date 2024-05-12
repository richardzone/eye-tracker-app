import os
import gettext
import argparse


def setup_localization():
    # Set up argument parsing for language selection
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="en", help="ISO code of the language to use")
    args, _ = parser.parse_known_args()

    # Set the language from the argument
    lang = args.lang

    # Set up gettext and translation based on command line argument
    locale_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "translations"
    )
    gettext.bindtextdomain("messages", locale_dir)
    gettext.textdomain("messages")
    translation = gettext.translation(
        "messages", locale_dir, languages=[lang], fallback=True
    )

    return translation.gettext, lang
