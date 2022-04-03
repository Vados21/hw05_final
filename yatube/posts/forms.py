from django.forms import ModelForm

from .models import Comment, Follow, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст',
            'group': 'Группа',
            'image': 'Изображение'
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст',
        }


class FollowForm(ModelForm):
    class Meta:
        model = Follow
        fields = ('author',)
        labels = {
            'author': 'Пользователь',
        }
