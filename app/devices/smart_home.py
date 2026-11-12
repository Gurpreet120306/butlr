from abc import ABC, abstractmethod
from typing import Any, Optional
import logging

from app.security.policy import ActionCategory, ActionRequest, AuthorizationStatus, SecurityPolicy

logger = logging.getLogger("BUTL-R.Devices.SmartHome")


class BaseSmartDevice(ABC):
    """Abstract base class for simulated smart-home devices."""

    def __init__(self, device_id: str, name: str, device_type: str):
        self.device_id = device_id
        self.name = name
        self.device_type = device_type

    @abstractmethod
    def get_state(self) -> dict[str, Any]:
        pass


class SmartLight(BaseSmartDevice):
    def __init__(self, device_id: str, name: str):
        super().__init__(device_id, name, "light")
        self.is_on = False
        self.brightness = 100

    def set_power(self, power: bool) -> None:
        self.is_on = power

    def set_brightness(self, level: int) -> None:
        self.brightness = max(0, min(100, level))

    def get_state(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "type": self.device_type,
            "is_on": self.is_on,
            "brightness": self.brightness,
        }


class SmartThermostat(BaseSmartDevice):
    def __init__(self, device_id: str, name: str, initial_temp: float = 22.0):
        super().__init__(device_id, name, "thermostat")
        self.target_temperature = initial_temp
        self.current_temperature = initial_temp
        self.mode = "auto"  # "heat", "cool", "auto", "off"

    def set_temperature(self, temp: float) -> None:
        self.target_temperature = round(temp, 1)

    def get_state(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "type": self.device_type,
            "target_temperature": self.target_temperature,
            "current_temperature": self.current_temperature,
            "mode": self.mode,
        }


class SmartLock(BaseSmartDevice):
    def __init__(self, device_id: str, name: str):
        super().__init__(device_id, name, "lock")
        self.is_locked = True

    def set_locked(self, locked: bool) -> None:
        self.is_locked = locked

    def get_state(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "type": self.device_type,
            "is_locked": self.is_locked,
        }


class DeviceHub:
    """Simulates smart-home control hub with security verification for physical devices."""

    def __init__(self, security_policy: Optional[SecurityPolicy] = None):
        self.security_policy = security_policy if security_policy is not None else SecurityPolicy()
        self.devices: dict[str, BaseSmartDevice] = {}

    def register_device(self, device: BaseSmartDevice) -> None:
        self.devices[device.device_id] = device

    def get_device(self, device_id: str) -> Optional[BaseSmartDevice]:
        return self.devices.get(device_id)

    def list_all_device_states(self) -> list[dict[str, Any]]:
        return [dev.get_state() for dev in self.devices.values()]

    def set_device_state(self, device_id: str, command: str, value: Any, user_confirmed: bool = False) -> tuple[bool, str]:
        """Apply state change to a device after security validation."""
        device = self.devices.get(device_id)
        if not device:
            return False, f"Device '{device_id}' not found."

        # Security check: Unlocking a door lock is sensitive and requires confirmation!
        if isinstance(device, SmartLock) and command == "unlock":
            req = ActionRequest(
                action_type="unlock_smart_device",
                category=ActionCategory.SYSTEM,
                target=device.name,
                requested_by="ai",
            )
            # Register permission if not already present
            if "unlock_smart_device" not in self.security_policy.permissions:
                self.security_policy.set_permission("unlock_smart_device", AuthorizationStatus.REQUIRES_CONFIRMATION)

            auth = self.security_policy.authorize(req)
            if auth.status == AuthorizationStatus.REQUIRES_CONFIRMATION and not user_confirmed:
                return False, f"Confirmation required to unlock '{device.name}'."

        if isinstance(device, SmartLight):
            if command == "power":
                device.set_power(bool(value))
                return True, f"Turned {device.name} {'ON' if device.is_on else 'OFF'}."
            elif command == "brightness":
                device.set_brightness(int(value))
                return True, f"Set {device.name} brightness to {device.brightness}%."

        elif isinstance(device, SmartThermostat) and command == "temp":
            device.set_temperature(float(value))
            return True, f"Set {device.name} to {device.target_temperature}°C."

        elif isinstance(device, SmartLock) and command in {"lock", "unlock"}:
            device.set_locked(command == "lock")
            return True, f"Successfully {'locked' if device.is_locked else 'unlocked'} {device.name}."

        return False, f"Unsupported command '{command}' for device '{device.name}'."
