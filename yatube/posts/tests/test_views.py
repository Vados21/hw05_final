from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from yatube.settings import PAGINATOR_LIST

from posts.models import Group, Post, Follow

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user')
        cls.group = Group.objects.create(
            title='Текст поста',
            slug='test_slug',
            description='Описание поста'
        )
        cls.group2 = Group.objects.create(
            title='Текст поста',
            slug='test_slug2',
            description='Описание поста'
        )
        Post.objects.bulk_create([
            Post(
                author=cls.user,
                text=f'Тестовый текст {num}',
                group=cls.group
            )
            for num in range(1, 21)]
        )
        cls.post = Post.objects.get(id=1)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_uses_correct_template(self):
        response = self.client.get(reverse('posts:index'))
        self.assertTemplateUsed(response, 'posts/index.html')

    def test_pages_uses_correct_template(self):
        post_id = PostPagesTests.post.id
        group_slug = PostPagesTests.group.slug
        user_test = PostPagesTests.user
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'slug': group_slug})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': user_test})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': post_id})
            ),
            'posts/create_post.html': reverse('posts:create_post'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_edit_page(self):
        post_id = PostPagesTests.post.id
        templates_pages_names = {
            'posts/create_post.html': (
                reverse('posts:post_edit', kwargs={'post_id': post_id}))
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:create_post'))
        form_fields = {
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_context_paginator(self):
        response = self.authorized_client.get(reverse('posts:index'))
        page_obj = response.context.get('page_obj')
        self.assertEqual(len(page_obj), PAGINATOR_LIST)

    def test_group_posts_context_paginator(self):
        group_slug = PostPagesTests.group.slug
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': group_slug}))
        self.assertEqual(len(response.context['page_obj']), PAGINATOR_LIST)

    def test_post_not_in_wrong_group(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', args=[PostPagesTests.group2.slug])
        )
        self.assertNotIn(self.post, response.context.get('page_obj'))

    def test_post_detail_pages_show_correct_context(self):
        post_id = PostPagesTests.post.id
        user_test = PostPagesTests.user
        post_text = PostPagesTests.post.text
        group_slug = PostPagesTests.group.slug
        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post_id})))
        self.assertEqual(response.context.get('post').author, user_test)
        self.assertEqual(response.context.get(
            'post').text, post_text)
        self.assertEqual(response.context.get('post').group.slug, group_slug)

    def test_post_create_context(self):
        response = self.authorized_client.get(reverse('posts:create_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_context(self):
        post_id = PostPagesTests.post.id
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post_id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def check_page_text_author_slug_context(self, object):
        obj_fileds = {
            object.text: self.post.text,
            object.author.username: self.author.username,
            object.group.slug: self.group.slug,
            object.group.description: self.group.description,
            object.group.title: self.group.title
        }
        for field, context in obj_fileds.items():
            with self.subTest(field=field):
                self.assertEqual(field, context)


class FinalProject(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(
            username='test_user',
            email='test_user@test.ru',
            password='12345'
        )
        self.follower = User.objects.create_user(
            username='testfollower',
            email='testfollower@test.ru',
            password='testpass1'
        )
        self.following = User.objects.create_user(
            username='testfollowing',
            email='testfollowing@test.ru',
            password='testpass2'
        )
        self.group = Group.objects.create(
            title='test',
            slug='test',
            description='test_group'
        )

    def test_image(self):
        self.client.force_login(self.user)
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04"
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )
        img = SimpleUploadedFile(
            "small.gif",
            small_gif,
            content_type="image/gif"
        )
        post = Post.objects.create(
            text='Test post with img',
            author=self.user,
            group=self.group,
            image=img
        )
        urls = (
            reverse('posts:index'),
            reverse('posts:profile', args=[post.author.username]),
            reverse('posts:post_detail', args=[post.pk]),
            reverse('posts:group_list', args=[self.group.slug]),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                paginator = response.context.get('paginator')
                if paginator is not None:
                    post = response.context['page'][0]
                else:
                    post = response.context['post']
                self.assertContains(response, '<img', status_code=200)
