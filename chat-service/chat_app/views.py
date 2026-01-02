from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import ChatMessage
from .middleware import get_user_from_token
from django.db.models import Max, Count, Q

class ChatHistoryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response({"detail": "Unauthorized"}, status=401)

        token = auth_header.split(" ")[1]
        user = get_user_from_token(token)

        if not user or "user_id" not in user:
            return Response({"detail": "Invalid token"}, status=401)

        role = user.get("role")
        if role == "vendor":
            customer_id = request.GET.get("user_id")
            if not customer_id:
                return Response({"detail": "user_id required"}, status=400)
            messages = ChatMessage.objects.filter(
                user_id=customer_id,
                vendor_id=user["vendor_id"]
            ).order_by("created_at")
        elif role == "customer":
            vendor_id = request.GET.get("vendor_id")
            if not vendor_id:
                return Response({"detail": "vendor_id required"}, status=400)
            messages = ChatMessage.objects.filter(
                user_id=user["user_id"],
                vendor_id=vendor_id
            ).order_by("created_at")
        else:
            return Response({"detail": "Invalid role"}, status=400)

        data = [
            {
                "id": msg.id,
                "message": msg.message,
                "sender": msg.sender_type,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ]
        return Response(data)


class MarkChatReadView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response({"detail": "Unauthorized"}, status=401)

        token = auth_header.split(" ")[1]
        user = get_user_from_token(token)

        if not user:
            return Response({"detail": "Invalid token"}, status=401)

        role = user.get("role")

        if role == "vendor":
            customer_id = request.data.get("user_id")
            if not customer_id:
                return Response({"detail": "user_id required"}, status=400)
            updated = ChatMessage.objects.filter(
                user_id=customer_id,
                vendor_id=user["vendor_id"],
                sender_type="customer",
                is_read=False
            ).update(is_read=True)
        elif role == "customer":
            vendor_id = request.data.get("vendor_id")
            if not vendor_id:
                return Response({"detail": "vendor_id required"}, status=400)
            updated = ChatMessage.objects.filter(
                user_id=user["user_id"],
                vendor_id=vendor_id,
                sender_type="vendor",
                is_read=False
            ).update(is_read=True)
        else:
            return Response({"detail": "Invalid role"}, status=400)

        return Response({"marked_read": updated})
    

class UnreadCountView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response({"detail": "Unauthorized"}, status=401)

        token = auth_header.split(" ")[1]
        user = get_user_from_token(token)

        if not user:
            return Response({"detail": "Invalid token"}, status=401)

        role = user.get("role")

        if role == "vendor":
            count = ChatMessage.objects.filter(
                vendor_id=user["vendor_id"],
                sender_type="customer",
                is_read=False
            ).count()
        elif role == "customer":
            count = ChatMessage.objects.filter(
                user_id=user["user_id"],
                sender_type="vendor",
                is_read=False
            ).count()
        else:
            return Response({"detail": "Invalid role"}, status=400)

        return Response({"unread_count": count})



class VendorInboxView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # 1️⃣ Auth
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response({"detail": "Unauthorized"}, status=401)

        token = auth_header.split(" ")[1]
        user = get_user_from_token(token)

        if not user or user.get("role") != "vendor":
            return Response({"detail": "Forbidden"}, status=403)

        vendor_id = user.get("vendor_id")
        if not vendor_id:
            return Response({"detail": "vendor_id missing"}, status=400)

        # 2️⃣ Find last message per user
        last_messages = (
            ChatMessage.objects
            .filter(vendor_id=vendor_id)
            .values("user_id")
            .annotate(
                last_time=Max("created_at")
            )
        )

        inbox = []

        # 3️⃣ For each conversation, collect details
        for row in last_messages:
            user_id = row["user_id"]

            last_message = ChatMessage.objects.filter(
                vendor_id=vendor_id,
                user_id=user_id
            ).order_by("-created_at").first()

            unread_count = ChatMessage.objects.filter(
                vendor_id=vendor_id,
                user_id=user_id,
                sender_type="customer",
                is_read=False
            ).count()

            inbox.append({
                "user_id": user_id,
                "last_message": last_message.message if last_message else "",
                "last_message_at": last_message.created_at.isoformat() if last_message else None,
                "unread_count": unread_count,
            })

        # 4️⃣ Sort by latest message
        inbox.sort(
            key=lambda x: x["last_message_at"] or "",
            reverse=True
        )

        return Response(inbox)