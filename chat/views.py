from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Message, Chatroom, RoomMessage
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from datetime import timedelta
from django.utils import timezone

# Smart emoji mapping — matches group name keywords to relevant emojis
KEYWORD_EMOJIS = {
    'python': '🐍', 'code': '💻', 'programming': '💻', 'dev': '👨‍💻', 'developer': '👨‍💻',
    'learn': '📚', 'study': '📖', 'class': '🎓', 'school': '🏫', 'education': '📝',
    'friend': '👫', 'buddy': '🤝', 'bestie': '💛', 'squad': '👥',
    'game': '🎮', 'gaming': '🎮', 'play': '🕹️',
    'music': '🎵', 'song': '🎶', 'band': '🎸', 'beat': '🥁',
    'vibe': '✨', 'chill': '😎', 'tribe': '🔥', 'zone': '🌀',
    'family': '🏠', 'home': '🏠', 'house': '🏡',
    'sport': '⚽', 'fitness': '💪', 'gym': '🏋️', 'cricket': '🏏', 'football': '⚽',
    'travel': '✈️', 'trip': '🧳', 'tour': '🗺️', 'adventure': '🏔️',
    'food': '🍕', 'cook': '👨‍🍳', 'kitchen': '🍳', 'eat': '🍽️',
    'movie': '🎬', 'film': '🎥', 'cinema': '🍿',
    'art': '🎨', 'design': '🖌️', 'creative': '🎭', 'draw': '✏️',
    'science': '🔬', 'math': '🧮', 'physics': '⚛️', 'chemistry': '🧪',
    'tech': '🤖', 'robot': '🤖', 'ai': '🧠', 'data': '📊',
    'work': '💼', 'office': '🏢', 'team': '🤜', 'project': '📋',
    'love': '❤️', 'heart': '💖', 'crush': '😍', 'couple': '💑',
    'nature': '🌿', 'garden': '🌻', 'plant': '🌱', 'flower': '🌸',
    'pet': '🐾', 'dog': '🐕', 'cat': '🐈', 'animal': '🦁',
    'photo': '📸', 'selfie': '🤳', 'camera': '📷',
    'book': '📚', 'read': '📖', 'novel': '📕', 'story': '📜',
    'night': '🌙', 'star': '⭐', 'moon': '🌙', 'dream': '💫',
    'chat': '💬', 'talk': '🗣️', 'gossip': '🤫', 'secret': '🤐',
    'fun': '🎉', 'party': '🥳', 'celebrate': '🎊', 'birthday': '🎂',
    'meme': '😂', 'funny': '🤣', 'joke': '😜', 'lol': '😆',
}

# Fallback emojis when no keyword matches
FALLBACK_EMOJIS = ['🏠', '🎮', '📚', '🎵', '🌟', '🎨', '🔥', '💎', '🌈', '🎯',
                   '🚀', '🦋', '🌸', '🎪', '🏝️', '🎭', '🧩', '🎲', '🌻', '🍀']

def get_room_emoji(room_id, room_name=''):
    """Match group name keywords to a relevant emoji, fallback to ID-based pick."""
    name_lower = room_name.lower()
    for keyword, emoji in KEYWORD_EMOJIS.items():
        if keyword in name_lower:
            return emoji
    return FALLBACK_EMOJIS[(room_id - 1) % len(FALLBACK_EMOJIS)]

def annotate_rooms_with_emoji(rooms):
    """Attach a unique emoji to each room."""
    for room in rooms:
        room.emoji = get_room_emoji(room.id, room.name)
    return rooms


# ─── Helper: build contacts with last message + unread count ───────────────
def get_contacts_with_meta(current_user):
    users = User.objects.all()
    contacts = []
    for user in users:
        last_msg = Message.objects.filter(
            Q(sender=current_user, receiver=user) |
            Q(sender=user, receiver=current_user)
        ).order_by('-timestamp').first()

        unread_count = Message.objects.filter(
            sender=user, receiver=current_user, is_read=False
        ).count() if user != current_user else 0

        contacts.append({
            'user': user,
            'last_message': last_msg,
            'unread_count': unread_count,
            'is_self': (user == current_user),
        })

    # Sort by most recent message first
    contacts.sort(
        key=lambda x: x['last_message'].timestamp.timestamp() if x['last_message'] else 0,
        reverse=True
    )
    return contacts


# ─── Room Chat ─────────────────────────────────────────────────────────────
@login_required(login_url='login')
def room_chat(request, room_id):
    room = get_object_or_404(Chatroom, id=room_id)
    if request.user not in room.members.all():
        return HttpResponseForbidden("You are not a member of this room.")
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            RoomMessage.objects.create(room=room, sender=request.user, content=content)
            return redirect('room_chat', room_id=room.id)
    messages = room.messages.all().order_by('timestamp')
    rooms = list(Chatroom.objects.filter(members=request.user))
    annotate_rooms_with_emoji(rooms)
    room.emoji = get_room_emoji(room.id, room.name)
    users = User.objects.all()
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)
    contacts = get_contacts_with_meta(request.user)
    return render(request, 'room_chat.html', {
        'room': room,
        'messages': messages,
        'rooms': rooms,
        'users': users,
        'contacts': contacts,
        'today': today,
        'yesterday': yesterday,
    })


# ─── Create Room ────────────────────────────────────────────────────────────
@login_required(login_url='login')
def create_room(request):
    if request.method == 'POST':
        name = request.POST.get('room_name')
        if name:
            room = Chatroom.objects.create(name=name, admin=request.user)
            room.members.add(request.user)
            return redirect('index')
    return render(request, 'create_room.html')


@login_required(login_url='login')
def start_chat_by_username(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        if username:
            user = User.objects.filter(username__iexact=username).first()
            if not user:
                # Auto-create user if they don't exist yet so new contact works instantly!
                user = User.objects.create_user(username=username, password='password123')
            return redirect('chat', receiver_id=user.id)
    return redirect('index')


# ─── Index ──────────────────────────────────────────────────────────────────
@login_required(login_url='login')
def index(request):
    rooms = list(Chatroom.objects.filter(members=request.user))
    annotate_rooms_with_emoji(rooms)
    users = User.objects.exclude(id=request.user.id)
    contacts = get_contacts_with_meta(request.user)
    context = {
        'users': users,
        'rooms': rooms,
        'contacts': contacts,
    }
    return render(request, 'index.html', context)


# ─── Add Member ─────────────────────────────────────────────────────────────
@login_required(login_url='login')
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


# ─── Manage Members ─────────────────────────────────────────────────────────
@login_required(login_url='login')
def manage_members(request, room_id):
    room = get_object_or_404(Chatroom, id=room_id)
    if request.user != room.admin:
        return HttpResponseForbidden("Only the room admin can manage members.")
    return render(request, 'chat/manage_members.html', {'room': room})


@login_required(login_url='login')
def leave_room(request, room_id):
    room = get_object_or_404(Chatroom, id=room_id)
    if request.user in room.members.all():
        room.members.remove(request.user)
    return redirect('index')


@login_required(login_url='login')
def delete_room(request, room_id):
    room = get_object_or_404(Chatroom, id=room_id)
    if request.user == room.admin:
        room.delete()
    return redirect('index')


# ─── Direct Chat ────────────────────────────────────────────────────────────
@login_required(login_url='login')
def chat(request, receiver_id):
    receiver = get_object_or_404(User, id=receiver_id)

    if request.method == 'POST':
        content = request.POST.get('message')
        if content:
            Message.objects.create(sender=request.user, receiver=receiver, content=content)

    # Mark incoming messages as read
    Message.objects.filter(
        sender=receiver, receiver=request.user, is_read=False
    ).update(is_read=True)

    messages = Message.objects.filter(
        Q(sender=request.user, receiver=receiver) |
        Q(sender=receiver, receiver=request.user)
    ).order_by('timestamp')

    users = User.objects.exclude(id=request.user.id)
    rooms = list(Chatroom.objects.filter(members=request.user))
    annotate_rooms_with_emoji(rooms)
    contacts = get_contacts_with_meta(request.user)

    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    return render(request, 'index.html', {
        'users': users,
        'rooms': rooms,
        'receiver': receiver,
        'messages': messages,
        'contacts': contacts,
        'today': today,
        'yesterday': yesterday,
    })


# ─── Auth ────────────────────────────────────────────────────────────────────
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── Message Actions ─────────────────────────────────────────────────────────
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if request.user != message.sender:
        return HttpResponseForbidden("You cannot delete this message.")
    message.is_deleted = True
    message.save()
    return redirect('chat', receiver_id=message.receiver.id)


@login_required
def edit_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if request.user != message.sender:
        return HttpResponseForbidden("You cannot edit this message.")
    if request.method == "POST":
        new_content = request.POST.get('content')
        if new_content:
            message.content = new_content
            message.is_edited = True
            message.save()
            return redirect('chat', receiver_id=message.receiver.id)
    return render(request, 'edit.html', {'message': message})



