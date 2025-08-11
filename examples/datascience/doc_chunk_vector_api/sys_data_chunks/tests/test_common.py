from sys_data_chunks.api import drop_low_rate_chunk
from sys_data_chunks.api import result_token_count
from sys_data_chunks.api import split_text


def test_split_text():
    """Simple tests for split_text"""
    text_data = "This is a simple sentence. Here is another one! And yet another; this should be the last."

    expected_result = [
        "This is a simple sentence",
        "Here is another one",
        "And yet another, this should be the last",
    ]

    result = list(split_text(text_data, chunk_size=20))
    assert result == expected_result, f"Expected {expected_result}, but got {result}"


def test_split_text_with_numbers():
    """Test for split_text with numbers"""
    text_data = (
        "This is a simple sentence. Here are some numbers: 1, 2, and 3.456."
        " Another set of numbers: 789, 0.123, and 456.789; this should be the last."
    )

    expected_result = [
        "This is a simple sentence, Here are some numbers: 1 2 and 3.456",
        "Another set of numbers: 789 0.123 and 456.789",
        "this should be the last"
    ]

    result = list(split_text(text_data, chunk_size=50))
    assert result == expected_result, f"Expected {expected_result}, but got {result}"


def test_drop_low_rate_chunk():
    """
    """
    data = {
        "doc": [
            {
                "data": "token1 token2 token3",
                "l2": 0.5,
                "cosine": 0.3,
            },
            {
                "data": "token4 token5 token6",
                "l2": 0.51,
                "cosine": 0.32,
            },
            {
                "data": "token7 token8 token9",
                "l2": 0.53,
                "cosine": 0.33,
            },
            {
                "data": "token10 token11 token12",
                "l2": 0.52,
                "cosine": 0.31,
            },
        ]
    }
    count1 = result_token_count(data)
    assert count1 == 12
    drop_low_rate_chunk(data)
    assert result_token_count(data) == 9
    assert data
    parts = []
    for items in data.values():
        for item in items:
            parts.append(item.get("data"))
    
    assert parts == [
        "token1 token2 token3",
        "token4 token5 token6",
        "token10 token11 token12",
    ]

    drop_low_rate_chunk(data)
    assert result_token_count(data) == 6
    parts.clear()
    for items in data.values():
        for item in items:
            parts.append(item.get("data"))

    assert parts == [
        "token1 token2 token3",
        "token4 token5 token6",
    ]
