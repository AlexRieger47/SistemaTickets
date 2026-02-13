from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'ticket_id', 'ticket_title', 'ticket_description', 'message', 'sent_at', 'read']
