# community/models.py

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    bid = models.ForeignKey('Block', null=True, on_delete=models.SET_NULL)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email
    

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    intro = models.TextField()
    photo_url = models.URLField(blank=True, null=True)


class Hood(models.Model):
    hname = models.CharField(max_length=100)

    def __str__(self):
        return self.hname


class Block(models.Model):
    hname = models.ForeignKey(Hood, on_delete=models.CASCADE)
    bname = models.CharField(max_length=100)
    description = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius = models.FloatField()

    def __str__(self):
        return self.bname

class Thread(models.Model):
    VISIBILITY_CHOICES = [
        ('neighbor', 'Neighbor'),
        ('friend', 'Friend'),
        ('block', 'Block'),
        ('hood', 'Hood'),
        ('private_friend', 'Private Friend'),
        ('private_neighbor', 'Private Neighbor'),
    ]
    creatorid = models.ForeignKey(CustomUser, related_name='created_threads', on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES)
    recipientid = models.ForeignKey(CustomUser, related_name='received_threads', on_delete=models.SET_NULL, null=True, blank=True)


class Message(models.Model):
    tid = models.ForeignKey(Thread, on_delete=models.CASCADE)
    uid = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    body = models.TextField()
    mlatitude = models.FloatField(null=True, blank=True)
    mlongitude = models.FloatField(null=True, blank=True)


class Friend(models.Model):
    uid1 = models.ForeignKey(CustomUser, related_name='friend1', on_delete=models.CASCADE)
    uid2 = models.ForeignKey(CustomUser, related_name='friend2', on_delete=models.CASCADE)
    status = models.CharField(max_length=10)

    class Meta:
        unique_together = ('uid1', 'uid2')


class Neighbor(models.Model):
    uid1 = models.ForeignKey(CustomUser, related_name='neighbor1', on_delete=models.CASCADE)
    uid2 = models.ForeignKey(CustomUser, related_name='neighbor2', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('uid1', 'uid2')


class FollowBlock(models.Model):
    uid = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    bid = models.ForeignKey(Block, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('uid', 'bid')


class MembershipApp(models.Model):
    uid = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    bid = models.ForeignKey(Block, on_delete=models.CASCADE)
    appstatus = models.CharField(max_length=10)
    count = models.IntegerField()


class MemberApproval(models.Model):
    appid = models.ForeignKey(MembershipApp, on_delete=models.CASCADE)
    approverid = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('appid', 'approverid')
