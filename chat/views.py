from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Message
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import logout
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.shortcuts import  HttpResponse
from .models import Chatroom, RoomMessage
from django.http import HttpResponseForbidden


def room_chat(request, room_id):
    room = get_object_or_404(Chatroom, id= room_id)
    if request.user not in room.members.all():
        return HttpResponse("Request Denied")
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            RoomMessage.objects.create(room = room , sender = request.user, content= content)
            return redirect('room_chat', room_id=room.id)
    messages = room.messages.all().order_by('timestamp')
    rooms = Chatroom.objects.filter(members=request.user)
    users = User.objects.all()
    return render(request, 'room_chat.html', {
        'room': room,
        'messages': messages,
        'rooms': rooms,
        'users': users,
    })



def create_room(request):
    if request.method == 'POST':
        name = request.POST.get('room_name')
        if name:
            room = Chatroom.objects.create(name=name, admin=request.user)
            room.members.add(request.user)
            return redirect('index')
    return render(request, 'create_room.html')



@login_required(login_url='login')
def index(request):
    rooms = Chatroom.objects.filter(members=request.user)
    users = User.objects.all()
    context = {
        'users':users,
        'rooms':rooms,
    }
    print(context)
    return render(request, 'index.html', context)


def add_member(request, room_id):
    room = get_object_or_404(Chatroom, id=room_id)
    if request.user != room.admin:
        return HttpResponseForbidden("Only the room admin can add members.")
    all_users = User.objects.exclude(id__in=room.members.all().values_list('id', flat=True))
    
    if request.method == "POST":
        user_id = request.POST.get('user_id')
        user_to_add = get_object_or_404(User, id=user_id)
        room.members.add(user_to_add)
        return redirect('room_chat', room_id=room.id)
        
    return render(request, 'chat/add_member.html', {'room': room, 'all_users': all_users})




def manage_members(request, room_id):
    room = get_object_or_404(Chatroom, id=room_id)
    return render(request, 'chat/manage_members.html', {'room': room})




@login_required
def chat(request, receiver_id):
    receiver = get_object_or_404(User, id=receiver_id)
    
    if request.method == 'POST':
        content = request.POST.get('message')
        if content:
         Message.objects.create(sender=request.user, receiver=receiver, content=content)
    
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=receiver) | 
        Q(sender=receiver, receiver=request.user)
    ).order_by('timestamp')
    
    users = User.objects.all()
    rooms = Chatroom.objects.filter(members=request.user)
    
    return render(request, 'index.html', {
        'users': users,
        'rooms': rooms,
        'receiver': receiver,
        'messages': messages
    })

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        initial_data = {'username': '','password1': '', 'password2': ''}
        form = UserCreationForm(initial = initial_data)
    return render(request, 'register.html', {'form': form})
 

# Login View
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        initial_data = {'username': '','password1': ''}
        form = AuthenticationForm(initial = initial_data)
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if request.user == message.sender:
        message.is_deleted = True
        message.save()


    return redirect('chat', receiver_id=message.receiver.id)


def edit_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    if request.user == message.sender:
        if request.method == "POST":
            new_content = request.POST.get('content')
            message.content = new_content
            message.is_edited = True
            message.save()

            return redirect('chat', receiver_id= message.receiver.id)
    return render(request, 'edit.html', {'message': message})


