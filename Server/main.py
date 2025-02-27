import os
import RPi.GPIO as GPIO
import adafruit_dht
import board
import time
import asyncio
import threading
from asyncio import sleep
from flask import Flask, jsonify, request
from flask_cors import CORS
from sinric import SinricPro, SinricProConstants

# Flask Setup
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow cross-origin requests

# GPIO Configuration
DHT_PIN = board.D14
LDR_PIN = 18
RELAY_PIN = 20

# Initialize DHT11 sensor
dht_device = adafruit_dht.DHT11(DHT_PIN)

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)

# Initial States
relay_status = False
automation_active = True

# Sinric Pro Configuration
APP_KEY = "c5092444-689e-4d1a-adfe-af9ce5247993"
APP_SECRET = "c9daee90-1189-4307-a8e0-600fd909dc73-1524acc2-48de-480b-b1b8-fd57adfd88bf"
TEMPERATURE_SENSOR_ID = "67bf1e69ff1f4eb6e763c5b0"
SWITCH_ID = "67bf743a77d346f8f47128c2"
AUTOMATION_SWITCH_ID = "67bf6b5eff1f4eb6e76412ba"

def speak(message):
    os.system(f"espeak -ven+m3 -s140 -p50 -a200 '{message}' --stdout | aplay")

# Function to measure light intensity
def read_ldr():
    reading = 0
    GPIO.setup(LDR_PIN, GPIO.OUT)
    GPIO.output(LDR_PIN, GPIO.LOW)
    time.sleep(0.1)  # Allow capacitor to discharge

    GPIO.setup(LDR_PIN, GPIO.IN)
    while GPIO.input(LDR_PIN) == GPIO.LOW:
        reading += 1  # Increment while capacitor charges

    return reading  # Higher value = darker environment


@app.route("/get-sensor-data", methods=["GET"])
def get_sensor_data():
    """Fetch the latest sensor readings and device states."""
    global relay_status, automation_active
    try:
        temperature = dht_device.temperature
        humidity = dht_device.humidity

        if temperature is None or humidity is None:
            return jsonify({"error": "Failed to retrieve sensor data"}), 500

        light_intensity = read_ldr()

        return jsonify({
            "temperature": temperature,
            "humidity": humidity,
            "bulbOn": relay_status,
            "automationOn": automation_active,
            "lightIntensity": light_intensity
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/set-bulb-state", methods=["POST"])
def set_bulb_state():
    """Set bulb state manually."""
    global relay_status, automation_active
    try:
        data = request.get_json()
        new_state = data.get("state")

        if new_state is not None:
            GPIO.output(RELAY_PIN, GPIO.HIGH if new_state else GPIO.LOW)
            relay_status = new_state
            automation_active = False
            speak("Turning bulb on" if new_state else "Turning bulb off")

            return jsonify({"message": "Bulb state updated", "bulbOn": relay_status, "automationOn": automation_active})
        else:
            return jsonify({"error": "Invalid state"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/set-automation-state", methods=["POST"])
def set_automation_state():
    """Enable or disable automation mode."""
    global automation_active
    try:
        data = request.get_json()
        new_state = data.get("state")

        if new_state is not None:
            automation_active = new_state
            speak("Automation is now active" if new_state else "Automation is now inactive")

            return jsonify({"message": "Automation state updated", "automationOn": automation_active})
        else:
            return jsonify({"error": "Invalid state"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Function to control the bulb based on light intensity
def control_bulb(light_intensity, threshold=3000):
    global relay_status
    if automation_active:  # Only control bulb if automation is active
        if light_intensity > threshold and not relay_status:
            GPIO.output(RELAY_PIN, GPIO.HIGH)  # Turn ON bulb
            relay_status = True
            print("Bulb ON (Low Light Detected)")
            speak("Turning bulb on")  # Voice output
            client.event_handler.raise_event(SWITCH_ID, SinricProConstants.SET_POWER_STATE, data={SinricProConstants.STATE: SinricProConstants.POWER_STATE_ON})
        elif light_intensity <= threshold and relay_status:
            GPIO.output(RELAY_PIN, GPIO.LOW)  # Turn OFF bulb
            relay_status = False
            print("Bulb OFF (Enough Light)")
            speak("Turning bulb off")  # Voice output
            client.event_handler.raise_event(SWITCH_ID, SinricProConstants.SET_POWER_STATE, data={SinricProConstants.STATE: SinricProConstants.POWER_STATE_OFF})

# Callback for Sinric Pro to manually control the bulb
def power_state(device_id, state):
    global relay_status, automation_active
    if device_id == SWITCH_ID:  # Only handle manual switch events for the bulb
        print(f"Device ID: {device_id}, State: {state}")
        if state == SinricProConstants.POWER_STATE_ON and not relay_status:
            GPIO.output(RELAY_PIN, GPIO.HIGH)  # Turn ON bulb
            relay_status = True
            print("Turning ON the bulb via Sinric Pro")
            speak("Turning bulb on")  # Voice output
        elif state == SinricProConstants.POWER_STATE_OFF and relay_status:
            GPIO.output(RELAY_PIN, GPIO.LOW)  # Turn OFF bulb
            relay_status = False
            print("Turning OFF the bulb via Sinric Pro")
            speak("Turning bulb off")  # Voice output
        # Set automation to inactive when the bulb is manually controlled
        automation_active = False
        print("Automation is now INACTIVE.")
        # Send event to update automation status in Sinric Pro
        client.event_handler.raise_event(
            AUTOMATION_SWITCH_ID,
            SinricProConstants.SET_POWER_STATE,
            data={SinricProConstants.STATE: SinricProConstants.POWER_STATE_OFF}  # Set automation state to OFF
        )
    else:
        automation_switch_state(device_id, state)

    return True, state

# Callback for Sinric Pro to toggle automation switch
def automation_switch_state(device_id, state):
    global automation_active
    if device_id == AUTOMATION_SWITCH_ID:  # Only handle automation switch events
        if state == SinricProConstants.POWER_STATE_ON:
            automation_active = True
            print("Automation is now ACTIVE.")
            speak("Automation is now active")  # Voice output
        elif state == SinricProConstants.POWER_STATE_OFF:
            automation_active = False
            print("Automation is now INACTIVE.")
            speak("Automation is now inactive")  # Voice output
    else:
        power_state(device_id, state)
    return True, state

callbacks = {
    SinricProConstants.SET_POWER_STATE: power_state,
    SinricProConstants.SET_POWER_STATE: automation_switch_state
}

# Event loop to read sensor data and send updates
async def events():
    while True:
        try:
            # Reading temperature and humidity from DHT11
            temperature = dht_device.temperature
            humidity = dht_device.humidity

            if temperature is not None and humidity is not None:
                print(f"Temperature: {temperature} C, Humidity: {humidity}%")
                client.event_handler.raise_event(
                    TEMPERATURE_SENSOR_ID,
                    SinricProConstants.CURRENT_TEMPERATURE,
                    data={
                        SinricProConstants.HUMIDITY: humidity,
                        SinricProConstants.TEMPERATURE: temperature
                    }
                )
            else:
                print("Failed to retrieve data from DHT11 sensor.")

            # Read LDR sensor and control the bulb based on light intensity
            light_intensity = read_ldr()
            print(f"Light Intensity: {light_intensity}")
            control_bulb(light_intensity)

        except RuntimeError as error:
            print(f"DHT11 reading error: {error}")
        except Exception as error:
            dht_device.exit()
            raise error

        await sleep(10)  # Wait 10 seconds before sending the next update

def start_flask():
    """Run Flask in a separate thread."""
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    client = SinricPro(
        APP_KEY, [SWITCH_ID, TEMPERATURE_SENSOR_ID, AUTOMATION_SWITCH_ID],
        callbacks, event_callbacks=events,
        enable_log=True, restore_states=False,
        secret_key=APP_SECRET
    )

    # Start Flask Server in a Separate Thread
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.start()

    # Start Sinric Pro WebSocket & Automation in the Main Thread
    try:
        loop.run_until_complete(client.connect())
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        dht_device.exit()
        GPIO.cleanup()
