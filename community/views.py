# community/views.py

# handles form submission, process data, perform actions, returns a response. 

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, ProfileForm, ProfileEditForm, ThreadForm, MessageForm
from .models import Profile, CustomUser, Thread, Message
from django.db import connection
from django.http import HttpResponse


## ---------Home----------- ##

def home_view(request):
    user_blocks = []
    recent_threads = {'neighbor': [], 'friend': [], 'block': [], 'hood': []}
    new_profiles = []
    unread_threads = []
    pending_applications = []
    search_results = []
    followed_blocks = []
    followed_block_threads = []
    all_blocks = []

    if request.user.is_authenticated:
        profile = get_object_or_404(Profile, user=request.user)

        # Fetch blocks the user is a member of
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT bid_id 
                FROM community_customuser 
                WHERE id = %s
            ''', [request.user.id])
            user_blocks = [row[0] for row in cursor.fetchall()]

        # Fetch recent threads for each visibility
        with connection.cursor() as cursor:
            # Fetch neighbor threads
            cursor.execute('''
                SELECT DISTINCT ON (t.id) t.id, t.subject, u.first_name, u.last_name, t.visibility
                FROM community_thread t
                JOIN community_customuser u ON t.creatorid_id = u.id
                JOIN community_neighbor n ON n.uid2_id = u.id
                WHERE t.visibility = 'neighbor' AND n.uid1_id = %s
                ORDER BY t.id DESC
                LIMIT 5;
            ''', [request.user.id])
            recent_threads['neighbor'] = cursor.fetchall()

            # Fetch friend threads
            cursor.execute('''
                SELECT DISTINCT ON (t.id) t.id, t.subject, u.first_name, u.last_name, t.visibility
                FROM community_thread t
                JOIN community_customuser u ON t.creatorid_id = u.id
                JOIN community_friend f ON (f.uid1_id = %s OR f.uid2_id = %s) AND (u.id = f.uid1_id OR u.id = f.uid2_id)
                WHERE t.visibility = 'friend' AND f.status = 'accepted'
                ORDER BY t.id DESC
                LIMIT 5;
            ''', [request.user.id, request.user.id])
            recent_threads['friend'] = cursor.fetchall()

            # Fetch block threads
            cursor.execute('''
                SELECT DISTINCT ON (t.id) t.id, t.subject, u.first_name, u.last_name, t.visibility
                FROM community_thread t
                JOIN community_customuser u ON t.creatorid_id = u.id
                WHERE t.visibility = 'block' AND u.bid_id = ANY(%s)
                ORDER BY t.id DESC
                LIMIT 5;
            ''', [user_blocks])
            recent_threads['block'] = cursor.fetchall()

            # Fetch hood threads
            cursor.execute('''
                SELECT DISTINCT ON (t.id) t.id, t.subject, u.first_name, u.last_name, t.visibility
                FROM community_thread t
                JOIN community_customuser u ON t.creatorid_id = u.id
                JOIN community_block b ON u.bid_id = b.id
                JOIN community_hood h ON b.hname_id = h.id
                WHERE t.visibility = 'hood' AND h.id IN (
                    SELECT h.id
                    FROM community_hood h
                    JOIN community_block b ON b.hname_id = h.id
                    WHERE b.id = ANY(%s)
                )
                ORDER BY t.id DESC
                LIMIT 5;
            ''', [user_blocks])
            recent_threads['hood'] = cursor.fetchall()

            # Fetch followed blocks
            cursor.execute('''
                SELECT b.id, b.bname
                FROM community_block b
                JOIN community_followblock f ON b.id = f.bid_id
                WHERE f.uid_id = %s
            ''', [request.user.id])
            followed_blocks = cursor.fetchall()

            # Fetch threads for the selected followed block
            followed_block_id = request.GET.get('followed_block')
            if followed_block_id:
                cursor.execute('''
                    SELECT DISTINCT ON (t.id) t.id, t.subject, u.first_name, u.last_name, t.visibility
                    FROM community_thread t
                    JOIN community_customuser u ON t.creatorid_id = u.id
                    WHERE t.visibility = 'block' AND u.bid_id = %s
                    ORDER BY t.id DESC
                    LIMIT 5;
                ''', [followed_block_id])
                followed_block_threads = cursor.fetchall()

            # Fetch all blocks except the user's current block
            cursor.execute('''
                SELECT b.id, b.bname
                FROM community_block b
                WHERE b.id != %s
            ''', [request.user.bid_id])
            all_blocks = cursor.fetchall()


        # Fetch new profiles in the user's blocks or hoods
        if user_blocks:
            with connection.cursor() as cursor:
                cursor.execute('''
                    SELECT p.id, p.first_name, p.last_name, p.intro, p.photo_url
                    FROM community_profile p
                    JOIN community_customuser u ON p.user_id = u.id
                    WHERE u.bid_id = ANY(%s)
                    ORDER BY u.date_joined DESC
                    LIMIT 5;
                ''', [user_blocks])
                new_profiles = cursor.fetchall()

        # Fetch unread messages
        if request.GET.get('unread') == 'true':
            with connection.cursor() as cursor:
                cursor.execute('''
                    SELECT t.id, t.subject, u.first_name, u.last_name, t.visibility, MAX(m.timestamp) as latest_message
                    FROM community_thread t
                    JOIN community_customuser u ON t.creatorid_id = u.id
                    JOIN community_message m ON t.id = m.tid_id
                    WHERE m.timestamp > %s
                    GROUP BY t.id, u.first_name, u.last_name, t.visibility
                    ORDER BY latest_message DESC;
                ''', [request.user.last_login])
                unread_threads = cursor.fetchall()

        # Fetch pending membership applications
        if user_blocks:
            with connection.cursor() as cursor:
                cursor.execute('''
                    SELECT ma.id, ma.uid_id, ma.bid_id, u.first_name, u.last_name, b.bname
                    FROM community_membershipapp ma
                    JOIN community_customuser u ON ma.uid_id = u.id
                    JOIN community_block b ON ma.bid_id = b.id
                    WHERE ma.appstatus = 'pending' AND ma.bid_id = ANY(%s)
                ''', [user_blocks])
                pending_applications = cursor.fetchall()


        # Handle keyword search
        keyword = request.GET.get('keyword')
        if keyword:
            with connection.cursor() as cursor:
                cursor.execute('''
                    SELECT DISTINCT m.id, m.title, m.body, m.timestamp, t.subject, t.visibility
                    FROM community_message m
                    JOIN community_thread t ON m.tid_id = t.id
                    LEFT JOIN community_friend f ON (f.uid1_id = %s OR f.uid2_id = %s) AND f.status = 'accepted'
                    LEFT JOIN community_neighbor n ON n.uid1_id = %s
                    LEFT JOIN community_customuser creator ON creator.id = t.creatorid_id
                    LEFT JOIN community_block b ON creator.bid_id = b.id
                    LEFT JOIN community_hood h ON b.hname_id = h.id
                    WHERE (m.body ILIKE %s)
                    AND (
                        (t.visibility = 'friend' AND (creator.id = f.uid1_id OR creator.id = f.uid2_id)) OR
                        (t.visibility = 'neighbor' AND creator.id = n.uid2_id) OR
                        (t.visibility = 'block' AND creator.bid_id = ANY(%s)) OR
                        (t.visibility = 'hood' AND h.id = ANY(%s)) OR
                        (t.visibility = 'private_friend' AND t.recipientid_id = %s) OR
                        (t.visibility = 'private_neighbor' AND t.recipientid_id = %s)
                    )
                    ORDER BY m.timestamp DESC;
                ''', [request.user.id, request.user.id, request.user.id, f'%{keyword}%', user_blocks, user_blocks, request.user.id, request.user.id])
                search_results = cursor.fetchall()

        # Handle geographical search
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        radius = request.GET.get('radius')
        if latitude and longitude and radius:
            with connection.cursor() as cursor:
                cursor.execute('''
                    SELECT DISTINCT m.id, m.title, m.body, m.timestamp, t.subject, t.visibility
                    FROM community_message m
                    JOIN community_thread t ON m.tid_id = t.id
                    JOIN community_customuser u ON u.id = m.uid_id
                    LEFT JOIN community_block b ON u.bid_id = b.id
                    LEFT JOIN community_hood h ON b.hname_id = h.id
                    LEFT JOIN community_friend f ON (f.uid1_id = %s OR f.uid2_id = %s) AND f.status = 'accepted'
                    LEFT JOIN community_neighbor n ON (n.uid1_id = %s)
                    WHERE (
                        3959 * acos(
                            cos(radians(%s)) * cos(radians(m.mlatitude))
                            * cos(radians(m.mlongitude) - radians(%s))
                            + sin(radians(%s)) * sin(radians(m.mlatitude))
                        ) * 5280 <= %s
                    ) AND (
                        t.visibility = 'public' OR
                        (t.visibility = 'block' AND u.bid_id = ANY(%s)) OR
                        (t.visibility = 'hood' AND h.id = ANY(%s)) OR
                        (t.visibility = 'friend' AND (
                            (f.uid1_id = %s AND m.uid_id = f.uid2_id) OR
                            (f.uid2_id = %s AND m.uid_id = f.uid1_id)
                        )) OR
                        (t.visibility = 'neighbor' AND (
                            (n.uid1_id = %s AND m.uid_id = n.uid2_id)
                        )) OR
                        (t.visibility = 'private_friend' AND t.recipientid_id = %s) OR
                        (t.visibility = 'private_neighbor' AND t.recipientid_id = %s)
                    );
                ''', [request.user.id, request.user.id, request.user.id, latitude, longitude, latitude, radius, user_blocks, user_blocks, request.user.id, request.user.id, request.user.id, request.user.id, request.user.id])
                search_results = cursor.fetchall()
        
    else:
        profile = None

    return render(request, 'home.html', 
                  {'recent_threads': recent_threads,
                   'profile': profile,
                   'new_profiles': new_profiles,
                   'unread_threads': unread_threads,
                   'pending_applications': pending_applications,
                   'search_results': search_results,
                   'show_unread': request.GET.get('unread') == 'true',
                   'followed_blocks': followed_blocks,
                    'followed_block_threads': followed_block_threads,
                    'all_blocks': all_blocks
                   }
                   )


## ---------User---------- ##

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            user = authenticate(email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


## ---------Profile----------- ##

@login_required
def create_profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.uid = request.user
            profile.save()
            return redirect('profile_detail', pk=profile.pk)
    else:
        form = ProfileForm()
    return render(request, 'create_profile.html', {'form': form})

@login_required
def profile_detail_view(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    return render(request, 'profile_detail.html', {'profile': profile})

@login_required
def edit_profile_view(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile_detail', pk=profile.pk)
    else:
        form = ProfileEditForm(instance=profile)
    return render(request, 'edit_profile.html', {'form': form})


## ---------Thread----------- ##

@login_required
def start_thread_view(request):
    if request.method == 'POST':
        thread_form = ThreadForm(request.POST)
        message_form = MessageForm(request.POST)
        if thread_form.is_valid() and message_form.is_valid():
            # Start a new thread
            with connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO community_thread (creatorid_id, subject, visibility)
                    VALUES (%s, %s, %s) RETURNING id
                ''', [request.user.id, thread_form.cleaned_data['subject'], thread_form.cleaned_data['visibility']])
                thread_id = cursor.fetchone()[0]
            
            # Post initial message to the new thread
            with connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO community_message (tid_id, uid_id, timestamp, title, body, mlatitude, mlongitude)
                    VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s) RETURNING id
                ''', [thread_id, request.user.id, message_form.cleaned_data['title'], message_form.cleaned_data['body'],
                      message_form.cleaned_data['mlatitude'], message_form.cleaned_data['mlongitude']])
                message_id = cursor.fetchone()[0]

            return redirect('home')
    else:
        thread_form = ThreadForm()
        message_form = MessageForm()

    return render(request, 'start_thread.html', {'thread_form': thread_form, 'message_form': message_form})

@login_required
def thread_detail_view(request, pk):
    thread = None
    messages = []

    # Fetch thread details with raw SQL
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT id, creatorid_id, subject, visibility, recipientid_id 
            FROM community_thread WHERE id = %s
        ''', [pk])
        thread = cursor.fetchone()

    # Fetch messages with raw SQL
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT id, tid_id, uid_id, timestamp, title, body, mlatitude, mlongitude 
            FROM community_message WHERE tid_id = %s
        ''', [pk])
        messages = cursor.fetchall()

    # Fetch creator name for the thread
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT first_name, last_name 
            FROM community_customuser WHERE id = %s
        ''', [thread[1]])
        creator = cursor.fetchone()

    thread_data = {
        'id': thread[0],
        'creator': f"{creator[0]} {creator[1]}",
        'subject': thread[2],
        'visibility': thread[3],
        'recipient_id': thread[4]
    }

    messages_data = [
        {
            'id': message[0],
            'thread_id': message[1],
            'user_id': message[2],
            'timestamp': message[3],
            'title': message[4],
            'body': message[5],
            'latitude': message[6],
            'longitude': message[7],
        }
        for message in messages
    ]

    return render(request, 'thread_detail.html', {'thread': thread_data, 'messages': messages_data})


@login_required
def reply_message_view(request, tid):
    thread = None

    # Fetch thread details with raw SQL
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT id, subject FROM community_thread WHERE id = %s
        ''', [tid])
        thread = cursor.fetchone()

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            # Post a reply to the thread
            with connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO community_message (tid_id, uid_id, timestamp, title, body, mlatitude, mlongitude)
                    VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s) RETURNING id
                ''', [tid, request.user.id, form.cleaned_data['title'], form.cleaned_data['body'],
                      form.cleaned_data['mlatitude'], form.cleaned_data['mlongitude']])
                message_id = cursor.fetchone()[0]

            return redirect('thread_detail', pk=tid)
    else:
        form = MessageForm()

    thread_data = {
        'id': thread[0],
        'subject': thread[1],
    }

    return render(request, 'reply_message.html', {'form': form, 'thread': thread_data})


## ---------Membership----------- ##

@login_required
def apply_to_block_view(request):
    if request.method == 'POST':
        block_id = request.POST.get('block_id')
        with connection.cursor() as cursor:
            # Create a new membership application
            cursor.execute('''
                INSERT INTO community_membershipapp (uid_id, bid_id, appstatus, count)
                VALUES (%s, %s, 'pending', 0)
            ''', [request.user.id, block_id])
        return redirect('home')
    return HttpResponse(status=405)  # Method not allowed

@login_required
@login_required
def approve_application_view(request, appid):
    if request.method == 'POST':
        with connection.cursor() as cursor:
            # Check if the approval record already exists
            cursor.execute('''
                SELECT 1
                FROM community_memberapproval
                WHERE appid_id = %s AND approverid_id = %s;
            ''', [appid, request.user.id])
            approval_exists = cursor.fetchone()

            if not approval_exists:
                # First, increment the count
                cursor.execute('''
                    UPDATE community_membershipapp
                    SET count = count + 1
                    WHERE id = %s
                    RETURNING count, uid_id, bid_id;
                ''', [appid])
                result = cursor.fetchone()
                count, uid, bid = result[0], result[1], result[2]

                # Check if count has reached 3
                if count >= 3:
                    # Approve the application
                    cursor.execute('''
                        UPDATE community_membershipapp
                        SET appstatus = 'approved'
                        WHERE id = %s;
                    ''', [appid])

                    # Update the user's bid if the application is approved
                    cursor.execute('''
                        UPDATE community_customuser
                        SET bid_id = %s
                        WHERE id = %s;
                    ''', [bid, uid])

                # Insert the approval record
                cursor.execute('''
                    INSERT INTO community_memberapproval (appid_id, approverid_id)
                    VALUES (%s, %s);
                ''', [appid, request.user.id])

        return redirect('home')
    return redirect('home')

