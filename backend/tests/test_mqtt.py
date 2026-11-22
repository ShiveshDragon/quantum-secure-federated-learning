from mqtt.payload import deserialize_message, serialize_message, update_topic, global_model_topic, key_status_topic

def test_payload_round_trip():
    m={"client_id":"c1","round":3,"value":12}; assert deserialize_message(serialize_message(m))==m

def test_topics():
    assert update_topic("c1")=="iot/fl/c1/update"
    assert global_model_topic()=="iot/fl/global_model"
    assert key_status_topic("c1")=="iot/qkd/c1/key_status"
