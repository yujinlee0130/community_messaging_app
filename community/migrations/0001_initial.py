# Generated by Django 5.0.4 on 2024-05-15 19:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Hood',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hname', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('first_name', models.CharField(blank=True, max_length=30)),
                ('last_name', models.CharField(blank=True, max_length=30)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Block',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bname', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('radius', models.FloatField()),
                ('hname', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='community.hood')),
            ],
        ),
        migrations.CreateModel(
            name='MembershipApp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appstatus', models.CharField(max_length=10)),
                ('count', models.IntegerField()),
                ('bid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='community.block')),
                ('uid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('intro', models.TextField()),
                ('photo_url', models.URLField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Thread',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255)),
                ('visibility', models.CharField(choices=[('neighbor', 'Neighbor'), ('friend', 'Friend'), ('block', 'Block'), ('hood', 'Hood'), ('private_friend', 'Private Friend'), ('private_neighbor', 'Private Neighbor')], max_length=20)),
                ('creatorid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_threads', to=settings.AUTH_USER_MODEL)),
                ('recipientid', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='received_threads', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('title', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('mlatitude', models.FloatField(blank=True, null=True)),
                ('mlongitude', models.FloatField(blank=True, null=True)),
                ('uid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('tid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='community.thread')),
            ],
        ),
        migrations.CreateModel(
            name='FollowBlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='community.block')),
                ('uid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('uid', 'bid')},
            },
        ),
        migrations.CreateModel(
            name='Friend',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=10)),
                ('uid1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='friend1', to=settings.AUTH_USER_MODEL)),
                ('uid2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='friend2', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('uid1', 'uid2')},
            },
        ),
        migrations.CreateModel(
            name='MemberApproval',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('approverid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('appid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='community.membershipapp')),
            ],
            options={
                'unique_together': {('appid', 'approverid')},
            },
        ),
        migrations.CreateModel(
            name='Neighbor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uid1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='neighbor1', to=settings.AUTH_USER_MODEL)),
                ('uid2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='neighbor2', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('uid1', 'uid2')},
            },
        ),
    ]