# Simple MQTT-based data collection client for the Kaa IoT platform.
# See https://docs.kaaiot.io/KAA/docs/current/Tutorials/getting-started/collecting-data-from-a-device/.

import json
import random
import signal
import string
import time

import paho.mqtt.client as mqtt

import sensors

KPC_HOST = "mqtt.cloud.kaaiot.com"  # Kaa Cloud plain MQTT host
KPC_PORT = 1883                     # Kaa Cloud plain MQTT port

ENDPOINT_TOKEN = "ilA2dAaXTD"       # Paste your endpoint token
APPLICATION_VERSION = "bvmq1ltbhnjc0btlkm7g-v1"  # Paste your application version

Irrigation = False
Target = 400

class DataCollectionClient:

    def __init__(self, client):
        self.client = client
        self.data_collection_topic = f'kp1/{APPLICATION_VERSION}/dcx/{ENDPOINT_TOKEN}/json'

        command_onoff_topic = f'kp1/{APPLICATION_VERSION}/cex/{ENDPOINT_TOKEN}/command/onoff/status'
        self.client.message_callback_add(command_onoff_topic, self.handle_onoff_command)
        self.command_onoff_result_topik = f'kp1/{APPLICATION_VERSION}/cex/{ENDPOINT_TOKEN}/result/onoff'

    def connect_to_server(self):
        print(f'Connecting to Kaa server at {KPC_HOST}:{KPC_PORT} using application version {APPLICATION_VERSION} and endpoint token {ENDPOINT_TOKEN}')
        self.client.connect(KPC_HOST, KPC_PORT, 60)
        print('Successfully connected')

    def disconnect_from_server(self):
        print(f'Disconnecting from Kaa server at {KPC_HOST}:{KPC_PORT}...')
        self.client.loop_stop()
        self.client.disconnect()
        print('Successfully disconnected')

    def compose_data_sample(self):
        data = sensors.get_data()
        global Irrigation
        global Target
        data['irrigation'] = Irrigation
        data['target'] = Target
        return json.dumps(data)

    def handle_onoff_command(self, client, userdata, message):
        print(f'<--- Received "on/off" command on topic {message.topic} \nProceeding...')
        command_result = self.compose_command_result_payload(message)
        print(f'command result {command_result}')
        client.publish(topic=self.command_onoff_result_topik, payload=command_result)
        # onoff commands
        global Irrigation
        if Irrigation:
            sensors.relay('off')
            Irrigation = False
        else:
            sensors.relay('on')
            Irrigation = True
        # With below approach we don't receive the command confirmation on the server side.
        # self.client.disconnect()
        # time.sleep(5)  # Simulate the reboot
        # self.connect_to_server()

    def compose_command_result_payload(self, message):
        command_payload = json.loads(str(message.payload.decode("utf-8")))
        print(f'command payload: {command_payload}')
        command_result_list = []
        for command in command_payload:
            commandResult = {"id": command['id'], "statusCode": 200, "reasonPhrase": "OK", "payload": "Success"}
            command_result_list.append(commandResult)
        return json.dumps(
            command_result_list
        )


def on_message(client, userdata, message):
    print(f'<-- Received message on topic "{message.topic}":\n{str(message.payload.decode("utf-8"))}')


def main():
    # Initiate server connection
    client = mqtt.Client(client_id=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6)))

    data_collection_client = DataCollectionClient(client)
    data_collection_client.connect_to_server()
    client.on_message = on_message

    # Start the loop
    client.loop_start()

    # Send data samples in loop
    listener = SignalListener()
    while listener.keepRunning:

        payload = data_collection_client.compose_data_sample()

        result = data_collection_client.client.publish(topic=data_collection_client.data_collection_topic, payload=payload)
        if result.rc != 0:
            print('Server connection lost, attempting to reconnect')
            data_collection_client.connect_to_server()
        else:
            print(f'--> Sent message on topic "{data_collection_client.data_collection_topic}":\n{payload}')

        time.sleep(3)

    data_collection_client.disconnect_from_server()


class SignalListener:
    keepRunning = True

    def __init__(self):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, signum, frame):
        print('Shutting down...')
        self.keepRunning = False


if __name__ == '__main__':
    main()
