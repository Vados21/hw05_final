from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post
from yatube.settings import PAGINATOR_LIST

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
        cls.follower = User.objects.create_user(
            username='testfollower',
            email='testfollower@test.ru',
            password='testpass1'
        )
        cls.following = User.objects.create_user(
            username='testfollowing',
            email='testfollowing@test.ru',
            password='testpass2'
        )

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

    def test_group_list_context(self):
        group_slug = PostPagesTests.group.slug
        group_title = PostPagesTests.group.title
        group_description = PostPagesTests.group.description
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': group_slug}))
        obj_1 = response.context['group']
        group_title_test = obj_1.title
        group_slug_test = obj_1.slug
        group_description_test = obj_1.description
        self.assertEqual(group_title_test, group_title)
        self.assertEqual(group_description_test, group_description)
        self.assertEqual(group_slug_test, group_slug)

    def test_follow(self):
        self.client.force_login(self.follower)
        self.client.post(reverse(
            'posts:profile_follow',
            kwargs={'username': self.following.username}
        ))
        self.assertEqual(Follow.objects.count(), 1)
        follow = Follow.objects.first()
        self.assertEqual(follow.author, self.following)
        self.assertEqual(follow.user, self.follower)

    def test_self_follow(self):
        self.client.force_login(self.follower)
        url_profile_follow = reverse(
            'posts:profile_follow',
            kwargs={'username': self.follower.username}
        )
        self.assertEqual(Follow.objects.all().count(), 0)
        self.client.get(url_profile_follow, follow=True)
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_unfollow(self):
        self.client.force_login(self.follower)
        self.follower = Follow.objects.create(
            user=self.follower,
            author=self.following
        )
        self.assertEqual(Follow.objects.all().count(), 1)
        self.client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.following.username}
        ))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_unauth_comments(self):
        post_id = 10
        self.text = 'Test comments'
        response = self.client.get(reverse(
            'posts:add_comment', kwargs={'post_id': post_id}),
            {'text': 'Comment'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 0)


class Sprint_final_tests(TestCase):
    def setUp(self):
        self.client = Client()
        self.client2 = Client()
        self.client_blogger = Client()
        self.user = User.objects.create_user(
            username='test'
        )
        self.user2 = User.objects.create_user(
            username='test1'
        )
        self.blogger = User.objects.create_user(
            username='blogger',
        )
        self.group = Group.objects.create(
            title='test',
            slug='test',
            description='test_group'
        )
        self.client.force_login(self.user)
        self.client2.force_login(self.user2)
        self.client_blogger.force_login(self.blogger)

    def test_follow_index(self):
        cache.clear()
        post = Post.objects.create(
            text='for followers',
            author=self.user
        )
        self.client.get(
            reverse('posts:profile_follow', args=[self.blogger.username]),
            follow=True
        )
        self.client_blogger.post(
            reverse('posts:create_post'),
            {'text': 'for followers'},
            follow=True
        )
        response = self.client.get(reverse('posts:follow_index'), follow=True)
        self.assertContains(
            response,
            post.text,
        )
        response = self.client2.get(reverse('posts:follow_index'), follow=True)
        self.assertNotContains(
            response,
            'for followers',
            msg_prefix='текст в ленте не от автора из подписки'
        )

    def test_cache(self):
        self.client.post(
            reverse('posts:create_post'),
            {'text': 'Пост для проверки кэша'}
        )
        response_index = self.client.get(reverse('posts:index'))
        index_content_1 = response_index.content
        post = response_index.context['page_obj'][0]
        self.assertEqual(post.text, 'Пост для проверки кэша')
        post.delete()
        response_index_2 = self.client.get(reverse('posts:index'))
        index_content_2 = response_index_2.content
        self.assertEqual(index_content_1, index_content_2, 'не работает')
        cache.clear()
        response_index_3 = self.client.get(reverse('posts:index'))
        index_content_3 = response_index_3.content
        self.assertNotEqual(index_content_1, index_content_3, 'не работает')

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
        post_detail_url = reverse('posts:post_detail', args=[1])
        urls = (
            reverse('posts:index'),
            reverse('posts:profile', args=[post.author.username]),
            reverse('posts:group_list', args=[self.group.slug]),
            post_detail_url
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                paginator = response.context.get('paginator')
                if paginator is not None:
                    post = response.context['page'][0]
                else:
                    if url == post_detail_url:
                        post = response.context['post']
                    else:
                        post = response.context['page_obj']
                self.assertContains(response, '<img', status_code=200)
