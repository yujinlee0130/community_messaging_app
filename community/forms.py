# community/forms.py

# defines the form fields and validation logic.

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, CustomUser, Block, Thread, Message
from django.db import connection

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    bid = forms.ModelChoiceField(queryset=Block.objects.all(), required=False)

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2', 'bid')

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.bid = self.cleaned_data['bid']

        if commit:
            user.set_password(self.cleaned_data['password1'])  # Set the password for hashing
            user.save(using=self._db)  # Save the user object to get the ID

            # Insert the profile using raw SQL
            self.save_profile_with_raw_sql(user)

        return user

    def save_profile_with_raw_sql(self, user):
        with connection.cursor() as cursor:
            cursor.execute('''
                INSERT INTO community_profile (user_id, first_name, last_name)
                VALUES (%s, %s, %s)
            ''', [user.id, user.first_name, user.last_name])


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'intro', 'photo_url']


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'intro', 'photo_url']

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            self.update_profile_with_raw_sql(profile)
        return profile

    def update_profile_with_raw_sql(self, profile):
        with connection.cursor() as cursor:
            cursor.execute('''
                UPDATE community_profile
                SET first_name = %s, last_name = %s, intro = %s, photo_url = %s
                WHERE id = %s
            ''', [profile.first_name, profile.last_name, profile.intro, profile.photo_url, profile.id])

class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['subject', 'visibility']

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['title', 'body', 'mlatitude', 'mlongitude']
