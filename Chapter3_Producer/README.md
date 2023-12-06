
# 카프카 프로듀서의 메시지 전송 절차 요약

- 카프카에 메시지를 쓰는 작업은 `ProducerRecord` 객체를 생성
- 키와 값 객체를 직렬화해서 바이트 배열로 변환
- 파티션을 명시적으로 지정하지 않았다면 파티셔너에게로 전달
- 파티셔너는 `ProducerRecord`객체의 키를 기준으로 파티션을 결정
- 같은 토픽의 파티션으로 전송될 레코드들은 레코드 배치(record batch)에 추가
- 별도 스레드가 이 레코드 배치를 적절한 카프카 브로커로 전송


# 프로듀서 생성시 3가지 필수 속성

- `bootstrap.servers`
  - 카프카 브로커의 `host:port` 목록
  - 모든 브로커를 포함할 필요는 없지만, 최소 2개 이상 지정할 것을 권장
- `key.serializer`
  - 카프카에 쓸 레코드의 키 값을 직렬화화기 위해 사용하는 시리얼라이저 클래스
  - 프로듀서 입장에서 키, 값 객체를 어떻게 바이트 배열로 바꿔야 하는지 알기 위한 목적
  - `ByteArraySerializer`, `StringSerializer`, `IntegerSerializer`, `VoidSerializer`
- `value.serializer`
  - 카프카에 쓸 레코드의 값을 직렬화하기 위해 사용하는 시리얼라이저 클래스

> Kafka Java Client를 기준으로 살펴보면, `KafkaProducer` 클래스의 생성자 파라미터가 `Map<String, Object> Config`, `Serializer<K> keySerializer`, `Serialzer<V> valueSerializer` 으로 정의되어 있다. 
> 하지만 confluent-kafka-python 라이브러리의 `Producer` 클래스는 `config: dict` 파라미터만 정의되어 있다는 점이 다르다. 


# 프로듀서가 메시지를 전송하는 3가지 방법

- Fire and Forget
  - 메시지를 브로커로 전송만 하고 성공, 실패 여부는 신경 쓰지 않는다. 
  - 전송 실패 메시지는 대부분 자동으로 재전송을 시도하지만, 재시도 할 수 없는 에러 또는 타임아웃이 발생한 경우 메시지가 유실된다.
- Synchronous Send (동기적 전송)
  - 보통 언제나 비동기적으로 작동하지만, `send()`메서드 호출 후 `get()`메서드를 호출해서 작업이 완료될 대까지 기다린다. 
  - 카프카 클러스터에 얼마나 작업이 몰리는지에 따라 이 시간 동안 아무것도 안 하면서 기다려야 하기 때문에 성능이 크게 낮아질 수 있다.
  - (TODO: 예제 해보기)
- Asynchronous Send (비동기적 전송)
  - 콜백 함수와 함께 `send()`메서드를 실행하면 브로커로부터 응답을 받는 시점에 자동으로 콜백 함수가 호출된다.
  - 카프카에 레코드를 쓴 뒤 해당 레코드의 토픽, 파티션, 오프셋을 반환하는데 보통 애플리케이션에서는 이런 메타데이터가 필요없다. 하지만 메시지 전송이 완전히 실패했을 때는 그 내용을 알아야 한다.
    - 메시지를 비동기적으로 전송하고도 에러를 처리하는 경우를 위해 프로듀서는 레코드를 전송할 때 콜백을 지정할 수 있다.
    - 콜백 안에서는 블로킹 작업을 수행하는 것은 권장하지 않는다.
  - (TODO: 예제 해보기)


# 프로듀서 설정

- `client.id`
  - 브로커가 프로듀서가 보내온 메시지를 서로 구분하기 위해 사용하는 값
- `acks`
  - 프로듀서가 쓰기 작업이 성공했다고 판별하기 위해 얼마나 많은 파티션 레플리카가 해당 레코드를 받아야 하는지 결정
    - 이는 전송되는 기록의 지속 시간을 제어한다. (This controls the durability of records that are sent)
  - 기본값은 리더가 해당 레코드를 받은 뒤 쓰기 작업이 성공했다고 응답하는 것 -> 상황에 따라 최적의 선택이 아닐 수 있다.
  - 설정값을 내려서 신뢰성을 낮추면 그만큼 레코드를 빠르게 보낼 수 있다.
- `acks=0`
  - 프로듀서는 메시지가 성공적으로 전달되었다고 간주하고 브로커의 응답을 기다리지 않는다. 
  - 브로커가 메시지를 전달 받지 못했을 경우 메시지가 유실된다. 
  - 매우 높은 처리량이 필요할 때 사용할 수 있다.
- `acks=1`
  - 프로듀서는 리더 레플리카가 메시지를 받으면 브로커로부터 성공했다는 응답을 받는다. 
  - 리더에 문제가 생긴다면 프로듀서는 에러 응답을 받을 것이고, 메시지 유실을 피하기 위해 재전송을 시도한다. 
- `acks=all or -1`
  - 프로듀서는 메시지가 모든 동기화 Replica(ISR)에 전달된 뒤에 브로커로부터 성공했다는 응답을 받는다. 
  - 가장 안전한 형태
  - acks=1보다 지연시간이 더 길어질 수 있다.
- 메시지 전달 시간 관련 설정
  - `send()`를 호출했을 때 성공 혹은 실패하기까지 얼마나 시간이 걸리는가?
  

![](https://www.conduktor.io/kafka/_next/image/?url=https%3A%2F%2Fimages.ctfassets.net%2Fo12xgu4mepom%2F18IoNzy4ocy0kMdyE5I4AE%2F023857fec700bdf8ff59d8971e5ce499%2FKafka_Producer_Retries_Delivery_Timeout_Process.png&w=3840&q=75)


- `max.block.ms`
  - `send()` 를 호출했을 때 최대 얼마나 오랫동안 블락될 수 있는지
    - 이 메서드는 프로듀서의 전송 버퍼가 가득 찼거나 브로커의 응답으로부터 메타데이터를 아직 사용 할 수 없기 때문에 블락될 수 있다. 
      - Serializer와 Partitioner에서의 블락은 이 시간에 포함되지 않는다. 
    - _confluent-kafka-python에서는 Producer 클래스에 이 설정은 존재하지 않는다._
- `delivery.timeout.ms`
  - 레코드가 배치에 저장된 시점부터 브로커의 응답을 받거나 전송을 포기하게 되는 시점까지의 제한시간
  - `linger.ms`와 `request.timeout.ms`보다 커야한다.
  - 레코드 배치가 전송을 기다리는 시간이 이 값을 넘어가면 타임아웃 예외와 함께 콜백이 호출
- `request.timeout.ms`
  - 프로듀서가 데이터를 전송할 때 서버로부터 응답을 받기 위해 얼마나 기다릴 것인지
- `retries`
  - 메시지를 재전송하는 횟수
- `retry.backoff.ms`
  - 재시도 사이 간격
  - 이 값과 `retries`를 직접 조정하는 것을 권장하지 않는다. `delivery.timeout.ms`를 조정하는 것을 추천
- `linger.ms`
  - 현재 배치를 전송하기 전까지 대기하는 시간
  - 프로듀서는 배치가 사이즈가 `batch.size`에 도달하지 않더라도 `linger.ms` 시간을 초과하면 배치를 전송
  - 기본적으로 전달할 메시지가 있는 경우 곧바로 전송하지만, 이 값을 0보다 크게 할 경우 전송 대기 시간은더 늘어나지만 배치 처리를 더 누적할 수 있어서 처리율이 증가한다. 
- `buffer.memory`
  - 메시지를 전송하기 전에 대기시키는 버퍼의 크기 (메모리 양)
- `compression.type`
  - 기본적으로 메시지는 압축하지 않음
  - 메시지를 압축할 압축 알고리즘 지정
- `batch.size`
  - 같은 파티션에 전송될 레코드가 저장되는 각 배치의 메모리 양 (bytes)
  - 프로듀서는 배치가 가득 찰 때까지 기다리지 않고 전송할 수 있기 때문에 이 값을 크게 설정한다고 해도 지연이 발생하지 않는다. 
  - 단, 이 값을 작게 설정할 경우 프로듀서의 오버헤드가 발생한다.
- `max.in.flight.requests.per.connection`
  - 프로듀서가 브로커로부터 응답을 받지 못한 상태에서 전송할 수 있는 최대 메시지 수 
  - 기본값은 5, 이 값이 1보다 큰 경우 메시지 순서가 뒤집어질 수 있다.
  - `enable.idempotence=true` 설정을 해야 순서 보장과 중복을 방지할 수 있다.
- `max.request.size`
  - 프로듀서가 전송하는 요청의 크기
  - 한 번의 요청에 보낼 수 있는 메시지의 최대 개수를 제한하는 의미
  - 브로커 또한 최대 메시지 크기를 결정하는 `message.max.bytes` 설정이 있는데 이 값을 동일하게 맞추는 게 좋다.
- `recieve.buffer.bytes`, `send.buffer.bytes`
  - 데이터를 읽거나 쓸 때 socket을 사용하는 경우 TCP 송수신 버퍼의 크기
  - -1일 경우, OS 기본값이 사용된다.
- `enable.idempotence`
  - 멱등적 프로듀서 기능
    - `max.in.flight.requests.per.connection` 은 5 이하, `retries`는 1 이상, `acks=all`로 설정해야 한다. 
  - 프로듀서가 레코드를 보낼 때마다 순차적인 번호를 붙여서 보게 된다. 


# 시리얼라이저

- 프로듀서를 설정할 때는 반드시 시리얼라이저를 지정해주어야 한다. 
- 즉, 카프카로 전송해야 하는 레코드를 Avro, Thrift, Protobuf와 같은 범용 직렬화 라이브러리(권장) 또는 커스텀 직렬화 로직을 구현해서 사용해야 한다. 
- 범용 직렬화 라이브러리를 권장하는 이유는 커스텀 직렬화 로직을 사용하면 회사 내 여러 팀에서 모두 동일한 커스텀 직렬화 로직을 사용하고 있어야 하기 때문이다.
- 혹시라도 동시에 코드를 변경해야 하는 상황이 발생할 수 있다는 것이다.


### Avro 

---

- JSON 형식으로 스키마를 정의한다. Avro로 직렬화한 데이터는 이진 파일 형태로 반환된다.
- Avro로 직렬화된 결과물을 읽거나 Avro로 직렬화할 때 스키마에 대한 정보가 별도로 주어진다는 것을 가정하고 있다.
- 따라서 Avro 파일 자체에 스키마를 직접 내장하는 형태로 사용된다. 
- Avro 스키마의 가장 큰 장점은 애플리케이션이 새로운 스키마로 전환하더라도 기존 스키마와 호환성을 유지할 수 있다는 점이다.


### 스키마 레지스트리

---

- Avro는 레코드를 읽을 때 스키마 전체가 필요하기 때문에 어딘가 스키마를 저장해둬야 한다. 
- 스키마 레지스트리는 아파치 카프카의 일부가 아닌 오픈소스 아키텍처이기 때문에 여러 오픈소스 구현체 중 하나를 골라서 사용하면 된다. 
- Confluent Platform을 설치하면 스키마 레지스트리가 포함되어 있다.
- 전체 스키마는 스키마 레지스트리에 저장되어 있기 때문에 카프카에서 쓰는 레코드에는 사용된 스키마의 고유 식별자만 포함시키면 된다. 


# 파티션

- 메시지의 Key의 기본값은 `null`이다. 하지만 Key는 하나의 토픽에 속한 여러 개의 파티션 중 해당 레코드가 저장될 파티션을 결정하는 기준이 된다.
  - 즉, 같은 Key를 가진 모든 메시지는 같은 파티션에 저장된다.
- **Key 값이 없는 (`null`) 경우**, 기본 파티셔너(partitioner)는 현재 사용 가능한 토픽의 파티션 중 하나를 랜덤으로 선택하고, 각 파티션별로 메시지 개수의 균형을 맞추기 위해 라운드 로빈 알고리즘을 사용한다. 

![](https://www.conduktor.io/kafka/_next/image/?url=https%3A%2F%2Fimages.ctfassets.net%2Fo12xgu4mepom%2F2b1gxvWBhd1MYaelXO5F9Y%2F7868246e76196c219450437d7b2ff540%2FRound_Robin__2_.png&w=3840&q=75)

- Kafka 2.4 버전 이상부터는 접착성(sticky) 처리를 하기 위한 라운드 로빈 알고리즘을 사용한다. 
  - 일단 키 값이 있는 메시지 뒤에 따라붙은 다음에 라운드 로빈 방식으로 배치된다.

![](https://www.conduktor.io/kafka/_next/image/?url=https%3A%2F%2Fimages.ctfassets.net%2Fo12xgu4mepom%2F4CZHPP89EKGQpI1GbsRHBZ%2F4dba2e74b59385093825d0e9df2a18f4%2FSticky_Partitioner_Batching__1_.png&w=3840&q=75)

- **Key 값이 있는 경우**, Key 값을 해시(hash)한 결과를 기준으로 저장할 파티션을 특정한다. 
- 특정한 Key 값에 대응되는 파티션은 파티션 수가 변하지 않는 한 변하지 않는다. 
  - 파티션을 결정하는데 사용되는 Key 값이 중요해서 저장될 파티션이 바뀌면 안 되는 경우
  - 해결책: 토픽의 파티션을 충분한 수로 크게 생성한 다음 더 이상 추가하지 않는다;;
- 커스텀 파티셔너
  - confluent-kafka-python 라이브러리로는 아직까지 커스텀 파티셔너를 개발할 수 없다. ([관련 이슈](https://github.com/confluentinc/confluent-kafka-python/issues/231) , 문제점: 파티셔너는 내부 librdkafka 스레드에서 호출될 수 있는데, 이 경우 Python 인터프리터에서 제대로 작동하지 않는다.)


# 인터셉터

- (대략적인 설명) 카프카 클라이언트의 코드를 고치지 않으면서 작동을 변경해야 하는 경우, (java) `ProducerInterceptor` 인터페이스를 구현한 클래스를 Producer를 실행할 때 설정값에 명시하는 방식으로 사용할 수 있다. 
- confluent-kafka-python 라이브러리의 코어 구현체인 librdkafka에는 Intercepter를 지원하지 않는다. ([관련 이슈](https://github.com/confluentinc/confluent-kafka-python/issues/181))


### 더 읽을거리

- [Confluent | Producer Config](https://docs.confluent.io/platform/current/installation/configuration/producer-configs.html)
- [Confluent | Kafka Producer](https://docs.confluent.io/platform/current/clients/producer.html)
- [Conduktor | Kafka Producers](https://www.conduktor.io/kafka/kafka-producers/)
- [Conduktor | Kafka Producer Retries](https://www.conduktor.io/kafka/kafka-producer-retries/)
- [Conduktor | # Producer Default Partitioner & Sticky Partitioner](https://www.conduktor.io/kafka/producer-default-partitioner-and-sticky-partitioner/)
- [언제나 김김 | 카프카 프로듀서](https://always-kimkim.tistory.com/entry/kafka101-producer)
- [Naver D2 | KafkaProducer Client Internals](https://d2.naver.com/helloworld/6560422)

