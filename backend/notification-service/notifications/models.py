from django.db import models


class Notification(models.Model):
    ticket_id = models.CharField(max_length=128, db_index=True)
    ticket_title = models.CharField(max_length=255, default='')
    ticket_description = models.TextField(default='')
    message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['-sent_at']),
            models.Index(fields=['read', '-sent_at']),
        ]

    def __str__(self):
        return f"Notification {self.id} - Ticket {self.ticket_id} - at {self.sent_at.strftime('%Y-%m-%d %H:%M:%S')}"
