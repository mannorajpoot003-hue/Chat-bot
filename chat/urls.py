from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name= 'index'),
    path('chat/<int:receiver_id>/', views.chat, name='chat'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('delete/<int:message_id>/', views.delete_message, name='delete'),
    path('edit/<int:message_id>/', views.edit_message, name='edit'),
    path('room_chat/<int:room_id>/',views.room_chat, name='room_chat'),
    path('create_room/', views.create_room, name='create_room'),
    path('room/<int:room_id>/add/', views.add_member, name='add_member'),
    path('room/<int:room_id>/manage/', views.manage_members, name='manage_members'),
    path('start_chat/', views.start_chat_by_username, name='start_chat'),
    path('room/<int:room_id>/leave/', views.leave_room, name='leave_room'),
    path('room/<int:room_id>/delete/', views.delete_room, name='delete_room'),
]


