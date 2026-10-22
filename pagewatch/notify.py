"""Notification channels. Each one is enabled by its environment variables."""

from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

import httpx

from pagewatch.config import Watch
from pagewatch.diff import Change

MAX_LINES = 15
TELEGRAM_LIMIT = 4000


@dataclass
class Alert:
    watch: Watch
    change: Change
    matched_keywords: list[str]

    @property
    def title(self) -> str:
        return f"pagewatch: '{self.watch.id}' changed"

    def body(self, max_lines: int = MAX_LINES) -> str:
        parts = [self.title, self.watch.url]
        if self.matched_keywords:
            parts.append("Keywords: " + ", ".join(self.matched_keywords))
        parts.append("")
        parts.extend(_section("+", self.change.added, max_lines))
        parts.extend(_section("-", self.change.removed, max_lines))
        return "\n".join(parts).rstrip()


def _section(sign: str, lines: list[str], max_lines: int) -> list[str]:
    out = [f"{sign} {line}" for line in lines[:max_lines]]
    if len(lines) > max_lines:
        out.append(f"{sign} ... and {len(lines) - max_lines} more line(s)")
    return out


class Notifier(Protocol):
    name: str

    def send(self, alert: Alert) -> None: ...


class ConsoleNotifier:
    name = "console"

    def send(self, alert: Alert) -> None:
        print(alert.body())
        print()


class TelegramNotifier:
    name = "telegram"

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id

    def send(self, alert: Alert) -> None:
        text = alert.body()
        if len(text) > TELEGRAM_LIMIT:
            text = text[: TELEGRAM_LIMIT - 20] + "\n... (truncated)"
        try:
            response = httpx.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={"chat_id": self.chat_id, "text": text, "disable_web_page_preview": True},
                timeout=20,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            # The bot token is part of the URL, so never surface the original error text in logs.
            status = f" (HTTP {exc.response.status_code})" if isinstance(exc, httpx.HTTPStatusError) else ""
            raise RuntimeError(f"Telegram API request failed: {type(exc).__name__}{status}") from None


class EmailNotifier:
    name = "email"

    def __init__(self, host: str, port: int, user: str, password: str, to: str, sender: str):
        self.host, self.port = host, port
        self.user, self.password = user, password
        self.to, self.sender = to, sender

    def send(self, alert: Alert) -> None:
        msg = EmailMessage()
        msg["Subject"] = alert.title
        msg["From"] = self.sender
        msg["To"] = self.to
        msg.set_content(alert.body(max_lines=100))
        with smtplib.SMTP(self.host, self.port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(self.user, self.password)
            smtp.send_message(msg)


def notifiers_from_env(env: dict[str, str] | None = None) -> list[Notifier]:
    env = dict(os.environ if env is None else env)
    notifiers: list[Notifier] = [ConsoleNotifier()]

    if env.get("TELEGRAM_BOT_TOKEN") and env.get("TELEGRAM_CHAT_ID"):
        notifiers.append(TelegramNotifier(env["TELEGRAM_BOT_TOKEN"], env["TELEGRAM_CHAT_ID"]))

    if all(env.get(k) for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "EMAIL_TO")):
        notifiers.append(
            EmailNotifier(
                host=env["SMTP_HOST"],
                port=int(env.get("SMTP_PORT") or 587),
                user=env["SMTP_USER"],
                password=env["SMTP_PASSWORD"],
                to=env["EMAIL_TO"],
                sender=env.get("EMAIL_FROM") or env["SMTP_USER"],
            )
        )
    return notifiers
