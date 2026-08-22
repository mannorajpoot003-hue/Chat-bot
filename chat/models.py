from django.db import models
from django.contrib.auth.models import User


class Chatroom(models.Model):
     name = models.CharField(max_length=100)
     admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_rooms')
     members = models.ManyToManyField(User, related_name='rooms')

     def __str__(self):
        return self.name
     

class RoomMessage(models.Model):
    room = models.ForeignKey(Chatroom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='requests_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='requests_received', on_delete=models.CASCADE )
    is_accepted = models.BooleanField(default=False)


class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} to {self.receiver.username}: {self.content[:20]}"

