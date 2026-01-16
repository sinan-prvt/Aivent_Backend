import pytest
import uuid
from .models import ChatMessage

@pytest.mark.django_db
class TestChatMessageModel:
    def test_create_message(self):
        msg_id = uuid.uuid4()
        msg = ChatMessage.objects.create(
            message_id=msg_id,
            user_id=1,
            vendor_id=1,
            sender_type="customer",
            message="Hello Test"
        )
        assert msg.message == "Hello Test"
        assert not msg.is_read
