from avmon.message import EndpointStatus


def test_message_conversion():
    msg = EndpointStatus(
        url="https://example.org/", reached=True, status=200, regex_match=None
    )
    assert msg == EndpointStatus.from_json(msg.to_json())
