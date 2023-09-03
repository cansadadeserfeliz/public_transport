from telegram import Update

from .services import get_application


def main() -> None:
    application = get_application()

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
