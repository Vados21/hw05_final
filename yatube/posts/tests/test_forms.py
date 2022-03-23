from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user')
        cls.group = Group.objects.create(
            title='Текст поста',
            slug='test_slug',
            description='Описание поста'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'test_text',
            'group': PostCreateFormTests.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': PostCreateFormTests.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=PostCreateFormTests.post.text,
                group=PostCreateFormTests.group.id
            ).latest('id')
        )

    def test_post_edit(self):
        post = PostCreateFormTests.post
        form_data = {
            'text': 'Был изменен текст',
            'group': post.group.id,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': post.id
                }
            ),
            data=form_data,
            follow=True
        )
        post.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
