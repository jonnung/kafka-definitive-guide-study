"""동기적인 메시지 전송과 비동기적 메시지 전송을 비교하는 프로듀서 예제

프로듀서는 메시지를 전송할 때, 동기적으로 전송할 수도 있고 비동기적으로 전송할 수도 있다.
동기적으로 전송하면 메시지가 전송될 때까지 블록되어 있다가 전송이 완료되면 다음 코드를 실행한다.
비동기적으로 전송하면 메시지가 전송되는 동안 블록되지 않고 다음 코드를 실행한다.

동기적으로 전송하는 방법은 produce() 메서드를 호출한 후 flush() 메서드를 호출하는 것이다.
flush() 메서드는 모든 메시지가 전송될 때까지 블록된다.

비동기적으로 전송하는 방법은 produce() 메서드를 호출한 후 flush() 메서드를 호출하지 않는 것이다.


이 예제는 동기적으로 메시지를 전송하는 예제이다.
비동기적 전송과 성능을 비교하기 위해 단순하게 브로커로 여러 메시지를 전송한 시간을 측정한다.

"""
import uuid
import time

from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import (
    StringSerializer,
    SerializationContext,
    MessageField,
)

import utils

from confluent_kafka import Producer


def main():
    config = utils.read_ccloud_config("ccloud_config.json")

    schema_str = utils.read_schema("users.avsc")
    schema_registry_client = SchemaRegistryClient(config["schema_registry"])

    key_serializer = StringSerializer("utf_8")
    value_serializer = AvroSerializer(schema_registry_client, schema_str)

    producer = Producer(config["broker"])

    dummy_users = []
    for i in range(1000):
        user_id = str(uuid.uuid4())
        dummy_users.append({"userId": user_id, "userName": f"Sample-{i}"})

    # 동기적으로 메시지를 전송하는 시간을 측정한다.
    synchronous_start_time = time.perf_counter_ns()
    for user in dummy_users:
        producer.produce(
            topic="users",
            key=key_serializer(user["userId"]),
            value=value_serializer(user, SerializationContext("users", MessageField.VALUE)),
        )

        # 프로듀서가 가진 모든 메시지가 브로커로 전달될 때까지 기다린다.
        producer.flush()

    synchronous_elapsed_time = (time.perf_counter_ns() - synchronous_start_time) / 1_000_000  # ns -> ms
    print(f"Synchronous send elapsed time: {synchronous_elapsed_time:.4f} ms")  # 샘플: 19533.8807 ms

    time.sleep(10)

    # 비동기적으로 메시지를 전송하는 시간을 측정한다.
    asynchronous_start_time = time.perf_counter_ns()
    for user in dummy_users:
        producer.produce(
            topic="users",
            key=key_serializer(user["userId"]),
            value=value_serializer(user, SerializationContext("users", MessageField.VALUE)),
        )

    asynchronous_elapsed_time = (time.perf_counter_ns() - asynchronous_start_time) / 1_000_000  # ns -> ms
    print(f"Asynchronous send elapsed time: {asynchronous_elapsed_time:.4f} ms")  # 샘플: 11.2048 ms


if __name__ == "__main__":
    main()
