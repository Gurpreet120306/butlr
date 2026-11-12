import unittest

from app.devices.smart_home import DeviceHub, SmartLight, SmartThermostat, SmartLock
from app.devices.mqtt_client import SimulatedMQTTClient
from app.devices.remote import SyncPayloadManager
from app.security.policy import SecurityPolicy


class TestDevicesAndEcosystem(unittest.TestCase):

    def setUp(self):
        self.policy = SecurityPolicy()
        self.hub = DeviceHub(security_policy=self.policy)

    def test_smart_light_controls(self):
        """Test turning smart light on/off and setting brightness level."""
        light = SmartLight(device_id="light_living_room", name="Living Room Light")
        self.hub.register_device(light)

        # Turn ON
        success, msg = self.hub.set_device_state("light_living_room", "power", True)
        self.assertTrue(success)
        self.assertTrue(light.is_on)

        # Set brightness
        success, msg = self.hub.set_device_state("light_living_room", "brightness", 75)
        self.assertTrue(success)
        self.assertEqual(light.brightness, 75)

    def test_smart_thermostat_controls(self):
        """Test setting target temperature on thermostat."""
        thermostat = SmartThermostat(device_id="thermo_main", name="Home Thermostat", initial_temp=21.0)
        self.hub.register_device(thermostat)

        success, msg = self.hub.set_device_state("thermo_main", "temp", 24.5)
        self.assertTrue(success)
        self.assertEqual(thermostat.target_temperature, 24.5)

    def test_smart_lock_requires_confirmation_to_unlock(self):
        """Unlocking a physical door lock is a sensitive operation requiring explicit user confirmation."""
        lock = SmartLock(device_id="door_front", name="Front Door")
        self.hub.register_device(lock)

        # Unconfirmed unlock attempt
        success, msg = self.hub.set_device_state("door_front", "unlock", True, user_confirmed=False)
        self.assertFalse(success)
        self.assertIn("Confirmation required", msg)
        self.assertTrue(lock.is_locked)

        # Confirmed unlock attempt
        success, msg = self.hub.set_device_state("door_front", "unlock", True, user_confirmed=True)
        self.assertTrue(success)
        self.assertFalse(lock.is_locked)

    def test_simulated_mqtt_publish_subscribe(self):
        """MQTT client publishes sensor messages and triggers registered callbacks."""
        mqtt = SimulatedMQTTClient()
        mqtt.connect()

        received_data = []

        def on_temp_sensor(topic, payload):
            received_data.append((topic, payload))

        mqtt.subscribe("sensors/living_room/temp", on_temp_sensor)
        mqtt.publish("sensors/living_room/temp", {"temperature": 23.4, "unit": "C"})

        self.assertEqual(len(received_data), 1)
        self.assertEqual(received_data[0][0], "sensors/living_room/temp")
        self.assertEqual(received_data[0][1]["temperature"], 23.4)

    def test_sync_payload_integrity(self):
        """Sync payload generates SHA256 checksum and verifies untampered state."""
        sync_mgr = SyncPayloadManager(device_name="Test Host")
        data = sync_mgr.create_sync_payload(
            conversations=[{"id": "conv_1"}],
            user_settings={"theme": "dark"},
        )

        self.assertTrue(sync_mgr.verify_sync_payload(data))

        # Tampered payload fails verification
        data["payload"]["settings"]["theme"] = "light"
        self.assertFalse(sync_mgr.verify_sync_payload(data))


if __name__ == "__main__":
    unittest.main()
