from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def test_page_author(self):
        response = self.client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def test_page_tech(self):
        response = self.client.get('/about/tech/')
        self.assertEqual(response.status_code, 200)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Текст поста',
            slug='test_slug',
            description='Описание поста'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{PostURLTests.group.slug}/',
            'posts/profile.html': f'/profile/{PostURLTests.user}/',
            'posts/post_detail.html': f'/posts/{PostURLTests.post.id}/',
            'posts/create_post.html': '/create/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, 200)

    def test_post_edit(self):
        post_id = PostURLTests.post.id
        response = self.authorized_client.get(f'/posts/{post_id}/edit/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_create_redirect_if_not_auth(self):
        response = self.client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_404_page(self):
        response = self.client.get('/wrong_url/')
        self.assertEqual(response.status_code, 404)
