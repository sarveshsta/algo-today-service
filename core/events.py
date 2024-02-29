import json
import uuid

from config.constants import SERVICE_NAME
from core.logger import FileLogger
from core.redis import PubSubClient

logger = FileLogger("pubsub_events.log")

CHANNEL_NAME = SERVICE_NAME


class NotEventException(Exception):
    """Exception raised when an dictionary cannot be parsed as a event object

    Args:
        Exception (str): Exception raised when an dictionary cannot be parsed as a event object

    Raises:

        Exception: Exception raised when an dictionary cannot be parsed as a event object

    Returns:
        _type_: NotEventException
    """
    ...


class Event:
    """
    Base class for all events.

    Attributes:
        event_type (str): The type of event.
    """

    event_type = None
    event_data = None

    def __init__(self, event_data):
        self.event_id = uuid.uuid4()
        self.event_data = event_data
        logger.log("info", f"{self}")

    def __str__(self):
        return f"[{self.event_id}] {self.event_type}: {self.event_data}"

    def to_dict(self):
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "event_data": self.event_data,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def get_event_type(self):
        """Get the type of event."""
        return self.event_type

    def activity(self):
        """Method to be implemented by subclasses."""
        raise NotImplementedError("Activity not implemented")


class SmartAPIEvent(Event):
    """Event related to SmartAPI."""

    event_type = "smartapi_event"

    def activity(self, pubsub: PubSubClient | None = None, data: dict | None = None):
        """Method to be implemented"""
        return pubsub.publish(CHANNEL_NAME, self.to_json())


class UserEvent(Event):
    """Event related to a user."""

    event_type = "user_event"


class StrategyEvent(Event):
    """Event related to a trading strategy."""

    event_type = "strategy_event"


class TradeEvent(Event):
    """Event related to a trade."""

    event_type = "trade_event"


def handle_activity(message: dict | bytes, pubsub: PubSubClient):
    data = message.get("data")
    if message.get("type") == "message" and isinstance(data, str):
        try:
            data = json.loads(data)
            event = None
            match data.get("event_type"):
                case "trade_event": event = TradeEvent(**data)
                case "strategy_event": event = StrategyEvent(**data)
                case "user_event": event = UserEvent(**data)
                case "smartapi_event": event = SmartAPIEvent(**data)
                case _: raise NotEventException("Couldn't parse event")
            print(event, pubsub)
        except json.JSONDecodeError:
            raise NotEventException("Could not parse message as JSON: {}".format(data))
