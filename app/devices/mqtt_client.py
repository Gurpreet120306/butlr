import json
import logging
from typing import Callable, Optional

logger = logging.getLogger("BUTL-R.Devices.MQTT")


class SimulatedMQTTClient:
    """Simulated local MQTT client for testing IoT and smart home sensors."""

    def __init__(self, broker_host: str = "localhost", port: int = 1883):
        self.broker_host = broker_host
        self.port = port
        self.is_connected = False
        self.subscriptions: dict[str, list[Callable[[str, dict], None]]] = {}
        self.published_messages: list[tuple[str, dict]] = []

    def connect(self) -> bool:
        """Connect to local simulated MQTT message broker."""
        self.is_connected = True
        logger.info(f"Connected to simulated MQTT broker at {self.broker_host}:{self.port}")
        return True

    def disconnect(self) -> None:
        self.is_connected = False
        logger.info("Disconnected from simulated MQTT broker.")

    def publish(self, topic: str, payload: dict) -> bool:
        """Publish an IoT sensor event or command."""
        if not self.is_connected:
            return False

        self.published_messages.append((topic, payload))
        logger.info(f"MQTT Publish | topic={topic} | payload={payload}")

        # Trigger internal subscribers for simulation
        if topic in self.subscriptions:
            for cb in self.subscriptions[topic]:
                cb(topic, payload)

        return True

    def subscribe(self, topic: str, callback: Callable[[str, dict], None]) -> None:
        """Subscribe to an IoT topic."""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(callback)
        logger.info(f"MQTT Subscribed to topic: {topic}")
