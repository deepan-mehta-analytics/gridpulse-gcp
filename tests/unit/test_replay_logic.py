from unittest.mock import MagicMock  # Mock objects standing in for real Pub/Sub subscriber/publisher clients

# Import the function under test — module does not exist yet, so this import fails first (RED)
from orchestrate.dags.bmrs_dlq_replay.replay_logic import replay_dlq_messages


def test_replay_dlq_messages_republishes_and_acks():
    # Test: one message sitting in the DLQ replay subscription gets republished onto the main topic and acked
    subscriber = MagicMock()  # Fake SubscriberClient — no real Pub/Sub call happens
    publisher = MagicMock()  # Fake PublisherClient — no real Pub/Sub call happens
    subscriber.subscription_path.return_value = (
        "projects/gridpulse-local/subscriptions/bmrs-bronze-dlq-replay"
    )  # Stub the resource-path builder to a known fixed string
    publisher.topic_path.return_value = "projects/gridpulse-local/topics/bmrs-bronze"  # Stub the topic-path builder

    fake_message = MagicMock()  # Fake PulledMessage wrapper returned by subscriber.pull
    fake_message.message.data = b'{"settlement_period": 1}'  # Raw bytes payload the DLQ message carries
    fake_message.ack_id = "ack-1"  # Ack ID used to acknowledge this message off the DLQ subscription
    subscriber.pull.return_value = MagicMock(received_messages=[fake_message])  # pull() returns a response with one message

    replayed = replay_dlq_messages(subscriber=subscriber, publisher=publisher)  # Call the function under test

    assert replayed == 1  # Exactly one message should have been replayed
    publisher.publish.assert_called_once_with(
        "projects/gridpulse-local/topics/bmrs-bronze", b'{"settlement_period": 1}'
    )  # Verify the message payload was republished to the main topic, unchanged
    subscriber.acknowledge.assert_called_once_with(
        request={
            "subscription": "projects/gridpulse-local/subscriptions/bmrs-bronze-dlq-replay",
            "ack_ids": ["ack-1"],
        }
    )  # Verify the replayed message was acked off the DLQ subscription


def test_replay_dlq_messages_returns_zero_when_empty():
    # Test: an empty DLQ replay subscription results in zero replays and no publish call
    subscriber = MagicMock()  # Fake SubscriberClient
    publisher = MagicMock()  # Fake PublisherClient
    subscriber.subscription_path.return_value = "sub-path"  # Stub the resource-path builder to a known fixed string
    subscriber.pull.return_value = MagicMock(received_messages=[])  # pull() returns a response with no messages

    assert replay_dlq_messages(subscriber=subscriber, publisher=publisher) == 0  # No messages replayed
    publisher.publish.assert_not_called()  # publish() must never be called when there is nothing to replay
