import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.unauth_client = Client()
        self.auth = PostCreateFormTests.user
        self.auth_client = Client()
        self.auth_client.force_login(self.auth)
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )

    def test_post_create(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Ещё один тестовый текст',
            'group': PostCreateFormTests.group.id,
            'author': PostCreateFormTests.user,
            'image': self.uploaded
        }
        response = self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={
                'username': PostCreateFormTests.user.username
            })
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        created_post = Post.objects.first()
        name = form_data['image'].name
        self.assertEqual(created_post.text, form_data['text'])
        self.assertEqual(created_post.author, form_data['author'])
        self.assertEqual(created_post.group.id, form_data['group'])
        self.assertEqual(created_post.image.name, 'posts/' + name)

    def test_post_edit_form(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        post_id = PostCreateFormTests.post.id
        form_data = {
            'text': 'Ещё один тестовый текст отредактирован',
            'group': PostCreateFormTests.group.id,
            'author': PostCreateFormTests.user
        }
        response = self.auth_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': post_id
            }),
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.get(id=post_id)
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group.id, form_data['group'])
        self.assertEqual(edited_post.author, form_data['author'])
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={
                'post_id': PostCreateFormTests.post.id
            })
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_unauth_user_can_not_create_post(self):
        """Неавторизованный пользователь не может создать запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Ещё один тестовый текст',
            'author': PostCreateFormTests.user
        }
        response = self.unauth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        first_redirect = reverse('users:login')
        next_redirect = reverse('posts:post_create')
        self.assertRedirects(
            response, first_redirect + f'?next={next_redirect}')
        self.assertEqual(Post.objects.count(), posts_count)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user
        )
        cls.comment = Comment.objects.create(
            text='Текст комментария',
            post=cls.post,
            author=cls.user
        )

    def setUp(self):
        self.unauth_client = Client()
        self.auth = CommentFormTests.user
        self.auth_client = Client()
        self.auth_client.force_login(self.auth)

    def test_comment_form(self):
        """Валидная форма создает запись в Comment."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария test',
            'post': CommentFormTests.post,
            'author': CommentFormTests.user
        }
        post_id = CommentFormTests.post.id
        response = self.auth_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': post_id
            }),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        created_comment = Comment.objects.first()
        self.assertEqual(created_comment.text, form_data['text'])
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={
                'post_id': post_id
            }
        ))

    def unauth_user_can_not_create_comment(self):
        """Неавторизованный пользователь не может создать запись в Comment."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария не существует',
            'post': CommentFormTests.post,
        }
        post_id = CommentFormTests.post.id
        response = self.unauth_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': post_id
            }),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        first_redirect = reverse('users:login')
        next_redirect = reverse('posts:add_comment')
        self.assertRedirects(
            response, first_redirect + f'?next={next_redirect}'
        )
