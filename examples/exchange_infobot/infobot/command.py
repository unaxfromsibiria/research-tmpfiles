from datetime import datetime, timedelta
import typing

import re

from .common import logger
from .storage import RateStorage
from .img_helper import create_image


search_parts = re.compile(r"\S+")


class Command:

    content: typing.List[str]
    storage: RateStorage
    clear_data: list = None

    def is_valid(self) -> bool:
        self.clear_data = self.content
        return True

    def setup(self, content: list) -> bool:
        self.content = content
        if self.clear_data:
            self.clear_data.clear()

        return self.is_valid()

    async def execute(self) -> typing.Tuple[str, typing.Union[bytes, None]]:
        return "enter command", None

    def __repr__(self) -> str:
        info = " ".join(self.content or ())
        return f"{self.__class__.__name__}({info})"


class HelpCommand(Command):
    """Info message.
    """

    async def execute(self) -> typing.Tuple[str, typing.Union[bytes, None]]:
        return """Commands:
        /list or /lst - returns list of all available rates
        /exchange $10 to CAD or  /exchange 10 USD to CAD - converts to the second currency with two decimal precision
        /history USD/CAD for 7 days - return an image graph chart which shows the exchange rate graph/chart of the selected currency for the last 7 days
        /help - get this message again
        """, None


class ShowListCommand(Command):
    """Show list.
    """

    def is_valid(self) -> bool:
        return (
            len(self.content) == 1 and
            self.content[0] in ("lst", "list")
        )

    async def execute(self) -> typing.Tuple[str, typing.Union[bytes, None]]:
        actual = await self.storage.is_rate_actual(self.storage.main_currency)
        err = None
        if not actual:
            n, err = await self.storage.update(self.storage.main_currency)
            if n > 0:
                logger.info(f"Updated from {self}")

        if err:
            result = err
        else:
            data = await self.storage.currency_rates()
            result = "\n".join(
                f"{currency}: {rate}"
                for currency, rate in sorted(data.items())
            )
        return result, None


class ExchangeCommand(Command):
    """Make exchange operation.
    """

    def is_valid(self) -> bool:
        n = len(self.content)
        expected = (
            n in (4, 5) and
            self.content[0] == "exchange"
        )
        if expected:
            value = curr = sep = target = None
            if n == 4:
                # $10 to CAD
                _, value, sep, target = self.content
                code = value[0]
                if code == "$":
                    curr = "USD"
                    value = float(value[1:])
            else:
                # 10 USD to CAD
                _, value, curr, sep, target = self.content
                value = float(value)

            expected = bool(
                value and
                sep == "to" and
                curr and len(curr) == 3 and
                target and len(target) == 3
            )
            if expected:
                self.clear_data = [value, curr, target]

        return expected

    async def execute(self) -> typing.Tuple[str, typing.Union[bytes, None]]:
        value, currency, target = self.clear_data
        actual = await self.storage.is_rate_actual(currency)
        err = None
        if not actual:
            n, err = await self.storage.update(currency)
            if n > 0:
                logger.info(f"Updated from {self}")

        if err:
            result = err
        else:
            new_value = await self.storage.convert(
                value=value, src=currency, target=target
            )
            if value != 0 and new_value == 0:
                result = f"Unknown targer currency {target} or {currency}"
                logger.info(f"{result} {self}")
            else:
                result = str(new_value)

        return result, None


class HistoryRateCommand(Command):
    """Make image with currency rate timeline chart.
    """

    def is_valid(self) -> bool:
        n = len(self.content)
        expected = (
            n == 6 and self.content[0] == "history"
        )
        if expected:
            _, curr1, curr2, sep, count, period = self.content
            count = int(count)
            expected = bool(
                count > 0 and
                period == "days" and
                sep == "for" and
                curr1 and len(curr1) == 3 and
                curr2 and len(curr2) == 3
            )
            if expected:
                self.clear_data = [count, curr1, curr2]

        return expected

    async def execute(self) -> typing.Tuple[str, typing.Union[bytes, None]]:
        count, currency_1, currency_2 = self.clear_data
        end = datetime.now().date()
        begin = end - timedelta(count)
        img = None
        data, err = await self.storage.request_history(
            begin=begin, end=end, target=currency_1, currency=currency_2
        )
        if err:
            result = err
        else:
            n = len(data)
            result = f"{n} values"
            if n > 0:
                img = create_image(data).read()

        return result, img


class CommamdHandler:

    commands: typing.List[Command] = [
        ShowListCommand(),
        ExchangeCommand(),
        HistoryRateCommand(),
        HelpCommand(),
    ]

    def __init__(self, storage: RateStorage):
        for cmd in self.commands:
            cmd.storage = storage

    def extract_parts(self, message: str) -> list:
        message = (message or "").strip()
        parts = []
        if message and message[0] == "/":
            parts.extend(search_parts.findall(message.replace("/", " ")))

        return parts

    async def execute(
        self, from_client: str, message: str
    ) -> typing.Tuple[str, typing.Union[bytes, None]]:
        """Get answer as text and an object.
        """
        parts = self.extract_parts(message)
        result = "", None
        for cmd in self.commands:
            cmd.setup(parts)
            try:
                is_valid = cmd.is_valid()
            except (ValueError, TypeError) as err:
                logger.warning(
                    f"In {cmd} from '{from_client}': {err}"
                )
                continue

            if is_valid:
                logger.info(f"From '{from_client}' new command: {cmd}")
                result = await cmd.execute()
                break

        return result
