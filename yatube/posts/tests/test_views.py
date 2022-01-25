import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.group_2 = Group.objects.create(
            title='Тестовый заголовок №2',
            slug='test-slug_2',
            description='Тестовое описание №2'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.index_url = ('posts:index', None)
        cls.group_url = ('posts:group_list', (cls.group.slug,))
        cls.profile_url = ('posts:profile', (cls.user.username,))
        cls.pages_urls = (
            cls.index_url,
            cls.group_url,
            cls.profile_url
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author = PostPagesTests.user
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_pages_uses_correct_templates(self):
        """view-функция использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:profile', kwargs={
                'username': self.user.username})): 'posts/profile.html',
            (reverse('posts:post_detail', kwargs={
                'post_id': self.post.id})): 'posts/post_detail.html',
            (reverse('posts:group_list', kwargs={
                'slug': 'test-slug'})): 'posts/group_list.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            (reverse('posts:post_edit', kwargs={
                'post_id': self.post.id})): 'posts/post_create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_posts_index_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:index'))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, PostPagesTests.post.text)
        self.assertEqual(post_author_0, PostPagesTests.user)
        self.assertEqual(post_group_0, PostPagesTests.group)
        self.assertEqual(post_image_0, PostPagesTests.post.image)
        self.assertIsInstance(response.context['page_obj'], Page)

    def test_group_list_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:group_list', kwargs={
                'slug': PostPagesTests.group.slug
            })
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, PostPagesTests.post.text)
        self.assertEqual(post_author_0, PostPagesTests.user)
        self.assertEqual(post_group_0, PostPagesTests.group)
        self.assertEqual(post_image_0, PostPagesTests.post.image)
        self.assertIsInstance(response.context.get('page_obj'), Page)
        self.assertEqual(response.context.get('group'), PostPagesTests.group)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:profile', kwargs={
                'username': PostPagesTests.user.username
            })
        )
        all_posts = PostPagesTests.user.posts.all()
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, PostPagesTests.post.text)
        self.assertEqual(post_author_0, PostPagesTests.user)
        self.assertEqual(post_group_0, PostPagesTests.group)
        self.assertEqual(post_image_0, PostPagesTests.post.image)
        self.assertIsInstance(response.context.get('page_obj'), Page)
        self.assertEqual(response.context.get('user_obj'), PostPagesTests.user)
        self.assertEqual(
            response.context.get('posts_number'), all_posts.count()
        )

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': PostPagesTests.post.id
            })
        )
        first_object = response.context['post_obj']
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, PostPagesTests.post.text)
        self.assertEqual(post_author_0, PostPagesTests.user)
        self.assertEqual(post_group_0, PostPagesTests.group)
        self.assertEqual(post_image_0, PostPagesTests.post.image)
        self.assertEqual(response.context.get('post_obj'), PostPagesTests.post)

    def test_post_create_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:post_edit', kwargs={
            'post_id': PostPagesTests.post.id
        }))
        self.assertEqual(response.context.get('post_obj'), PostPagesTests.post)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_displayed_on_correct_pages(self):
        """
            Созданный пост отображается на страницах группы,
            пользователя и главной странице
        """
        for name, args in PostPagesTests.pages_urls:
            with self.subTest(name=name):
                response = self.author_client.get(
                    reverse(name, args=args)
                )
                self.assertIn(
                    PostPagesTests.post, response.context.get('page_obj')
                )

    def test_post_not_in_a_wrong_group(self):
        """Созданный пост не попал не в свою группу"""
        response = self.author_client.get(
            reverse('posts:group_list', kwargs={
                'slug': PostPagesTests.group_2.slug
            })
        )
        self.assertNotIn(
            PostPagesTests.post, response.context.get('page_obj')
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.index_url = ('posts:index', None)
        cls.group_url = ('posts:group_list', (cls.group.slug,))
        cls.profile_url = ('posts:profile', (cls.user.username,))
        cls.paginator_urls = (
            cls.index_url,
            cls.group_url,
            cls.profile_url
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(PaginatorViewsTest.user)
        self.all_posts = 13
        self.second_page_nmbr = self.all_posts % settings.POST_NUMBER
        posts = [
            Post(
                text=f'Test text №{i}',
                author=PaginatorViewsTest.user,
                group=PaginatorViewsTest.group
            ) for i in range(1, self.all_posts + 1)
        ]
        Post.objects.bulk_create(posts)

    def test_paginator_posts_on_pages(self):
        """Paginator отображает корректное число постов на страницах"""
        pages = {
            1: settings.POST_NUMBER,
            2: self.second_page_nmbr
        }
        for name, args in PaginatorViewsTest.paginator_urls:
            for page, length in pages.items():
                with self.subTest(page=page, name=name):
                    response = self.author_client.get(
                        reverse(name, args=args), {'page': page}
                    )
                    self.assertEqual(
                        len(response.context['page_obj'].object_list), length
                    )


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='follower')
        cls.author = User.objects.create_user(username='author')

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(FollowTests.author)
        self.user_client = Client()
        self.user_client.force_login(FollowTests.user)
        self.guest_client = Client()

    def test_authorized_can_follow(self):
        """Авторизованные пользователи могут подписываться друг на друга"""
        count_follow = Follow.objects.count()
        self.user_client.get(
            reverse('posts:profile_follow', kwargs={
                'username': FollowTests.author.username
            })
        )
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        follow_obj = Follow.objects.first()
        self.assertEqual(follow_obj.author, FollowTests.author)
        self.assertEqual(follow_obj.user, FollowTests.user)

    def test_authorized_can_unfollow(self):
        """Авторизованные пользователи могут отписываться друг от друга"""
        self.user_client.get(
            reverse('posts:profile_follow', kwargs={
                'username': FollowTests.author.username
            })
        )
        count_follow = Follow.objects.count()
        self.user_client.get(
            reverse('posts:profile_unfollow', kwargs={
                'username': FollowTests.author.username
            })
        )
        self.assertEqual(Follow.objects.count(), count_follow - 1)

    def test_unauth_user_can_not_follow(self):
        """Неавторизованный пользователь не может создать запись в Follow."""
        count_follow = Follow.objects.count()
        response = self.guest_client.get(
            reverse('posts:profile_follow', kwargs={
                'username': FollowTests.author.username
            })
        )
        first_redirect = reverse('users:login')
        next_redirect = reverse('posts:profile_follow', kwargs={
            'username': FollowTests.author.username
        })
        self.assertEqual(Follow.objects.count(), count_follow)
        self.assertRedirects(
            response, first_redirect + f'?next={next_redirect}'
        )

    def test_follow_index_contains_new_posts(self):
        """
        Новая запись пользователя появляется в ленте подписчиков
        и не появляется в ленте тех, кто на него не подписан.
        """
        another_user = User.objects.create_user(username='another')
        another_client = Client()
        another_client.force_login(another_user)
        self.user_client.get(
            reverse('posts:profile_follow', kwargs={
                'username': FollowTests.author.username
            })
        )
        new_post = Post.objects.create(
            text='Текст для проверки подписки',
            author=FollowTests.author
        )
        response = self.user_client.get(reverse(
            'posts:follow_index'
        ))
        self.assertIn(
            new_post, response.context.get('page_obj')
        )
        response_2 = another_client.get(reverse(
            'posts:follow_index'
        ))
        self.assertNotIn(
            new_post, response_2.context.get('page_obj')
        )
