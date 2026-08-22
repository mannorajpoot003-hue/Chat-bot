from django.contrib import admin
from .models import Message
from .models import Chatroom, RoomMessage
# Register your models here.

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'content', 'timestamp')
    
    search_fields = ('content', 'sender__username', 'receiver__username')
    list_filter = ('timestamp', 'sender')
    actions = ['delete_selected'] 


@admin.register(RoomMessage)
class RoomMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'room', 'content', 'timestamp') 
    search_fields = ('content', 'sender__username', 'room__name')
    list_filter = ('timestamp', 'room', 'sender')


@admin.register(Chatroom)
class ChatroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'admin', )



