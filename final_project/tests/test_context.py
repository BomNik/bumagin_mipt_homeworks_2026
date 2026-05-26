from gigavibe.context import ChatHistory, Message, total_content_length


def test_chat_history_stores_messages_in_order() -> None:
    history = ChatHistory()

    history.add_user('hello')
    history.add_assistant('hi')

    assert history.to_list() == [
        Message(role='user', content='hello'),
        Message(role='assistant', content='hi'),
    ]


def test_limit_message_removes_oldest_messages() -> None:
    history = ChatHistory(
        [
            Message(role='user', content='first'),
            Message(role='assistant', content='second'),
            Message(role='user', content='third'),
        ],
    )

    history.trim(limit_message=2, limit_chars=None, system_prompt='')

    assert history.to_list() == [
        Message(role='assistant', content='second'),
        Message(role='user', content='third'),
    ]


def test_limit_chars_removes_oldest_messages_until_history_fits_budget() -> None:
    history = ChatHistory(
        [
            Message(role='user', content='12345'),
            Message(role='assistant', content='abc'),
            Message(role='user', content='xy'),
        ],
    )

    history.trim(limit_message=None, limit_chars=5, system_prompt='')

    assert history.to_list() == [
        Message(role='assistant', content='abc'),
        Message(role='user', content='xy'),
    ]
    assert total_content_length(history.to_list()) == 5


def test_limit_chars_counts_system_prompt() -> None:
    history = ChatHistory(
        [
            Message(role='user', content='old'),
            Message(role='assistant', content='new'),
        ],
    )

    history.trim(limit_message=None, limit_chars=8, system_prompt='sys')

    assert history.to_list() == [
        Message(role='assistant', content='new'),
    ]


def test_too_long_single_message_is_trimmed_from_left() -> None:
    history = ChatHistory([Message(role='user', content='hello world')])

    history.trim(limit_message=None, limit_chars=5, system_prompt='')

    assert history.to_list() == [Message(role='user', content='world')]


def test_too_long_single_message_respects_system_prompt_budget() -> None:
    history = ChatHistory([Message(role='user', content='hello world')])

    history.trim(limit_message=None, limit_chars=8, system_prompt='sys')

    assert history.to_list() == [Message(role='user', content='world')]


def test_zero_history_budget_clears_history() -> None:
    history = ChatHistory([Message(role='user', content='hello')])

    history.trim(limit_message=None, limit_chars=3, system_prompt='sys')

    assert history.to_list() == []


def test_both_limits_are_applied() -> None:
    history = ChatHistory(
        [
            Message(role='user', content='first'),
            Message(role='assistant', content='second'),
            Message(role='user', content='third'),
        ],
    )

    history.trim(limit_message=2, limit_chars=6, system_prompt='')

    assert history.to_list() == [Message(role='user', content='third')]
