from django.conf import settings
from django.conf.urls import (
    include,
    url,
)

from rest_framework import (
    permissions,
    routers,
    serializers,
    status,
)
from rest_framework.decorators import detail_route
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from fb_emails import models as fb_emails_models
from fb_github import models
from firebot.api import BaseSerializer


################################################################################
# Serializers
################################################################################

class EmailMapSerializer(BaseSerializer):
    login = serializers.SlugField()

    class Meta:
        model = models.EmailMap
        fields = (
            'email',
            'login',
            'repo',
            'url',
        )
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=models.EmailMap.objects.all(),
                fields=('repo', 'email'),
                message='Email address is already in use.',
            )
        ]
        extra_kwargs = {
            'repo': {
                'lookup_field': 'uuid',
                'lookup_url_kwarg': 'uuid',
             },
        }

    def update(self, instance, validated_data):
        # Not allowed to update repo.
        validated_data.pop('repo', None)
        return super().update(instance, validated_data)


class RepositorySerializer(serializers.HyperlinkedModelSerializer):
    emailmap_set = EmailMapSerializer(many=True, read_only=True)
    urls = serializers.SerializerMethodField()

    class Meta:
        model = models.Repository
        fields = (
            'emailmap_set',
            'email',
            'email_slug',
            'full_name',
            'login',
            'name',
            'status',
            'url',
            'urls',
        )
        read_only_fields = [f for f in fields if f != 'email_slug']
        extra_kwargs = {
            'email_slug': {
                'required': True,
            },
            'url': {
                'lookup_field': 'uuid',
                'lookup_url_kwarg': 'uuid',
             },
        }

    def validate_email_slug(self, value):
        if value in settings.FIREBOT_BANNED_EMAIL_SLUGS:
            raise serializers.ValidationError('"{}" is not permitted.'.format(value))
        return value

    def get_urls(self, obj):
        return {
            'github': obj.gh_url,
            'emailmap_add': reverse('emailmap-list', request=self.context['request']),
            'purge_attachments': reverse('repository-purge-attachments', args=[obj.uuid], request=self.context['request']),
        }


class RepositoryApproveSerializer(RepositorySerializer):
    class Meta(RepositorySerializer.Meta):
        fields = (
            'full_name',
            'inviter_login',
            'login',
            'name',
            'status',
            'url',
        )
        read_only_fields = fields


################################################################################
# Viewsets
################################################################################

class EmailMapViewSet(
    CreateModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    queryset = models.EmailMap.objects.all()
    serializer_class = EmailMapSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        return (super(EmailMapViewSet, self).get_queryset()
            .filter(repo__admins=self.request.user)
        )


class RepositoryViewSet(
    RetrieveModelMixin,
    ListModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'
    permission_classes = (permissions.IsAuthenticated, )
    queryset = models.Repository.objects.all()
    serializer_class = RepositorySerializer

    def get_queryset(self):
        return (super(RepositoryViewSet, self).get_queryset()
            .active()
            .filter(admins=self.request.user)
        )

    def dispatch(self, request, *args, **kwargs):
        # Workaround to skip authentication checking for the approve view
        if request.resolver_match.url_name == 'repository-approve':
            self.permission_classes = (permissions.AllowAny, )

        return super().dispatch(request, *args, **kwargs)

    @detail_route(methods=['post'])
    def purge_attachments(self, request, uuid=None):
        repo = self.get_object()

        qs = fb_emails_models.Attachment.objects.filter(
            msg__issue__repo=repo
        )
        for attachment in qs.iterator():
            attachment.file.delete()
            attachment.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post'])
    def approve(self, request, uuid=None):
        # We can't use `self.get_object()` because:
        # 1) It filters only for active repos and this one is potentially
        #    not active yet
        # 2) We want to always return a response even if the current user
        #    does not have access to this particular repo
        repo = get_object_or_404(models.Repository, uuid=uuid)

        # See if we're going to approve this repo
        if ((repo.status == models.Repository.Status.PendingInviterApproval) and
            (repo.inviter_login == request.user.username)):
            repo.approve_by_inviter(request.user)

        # Select which serializer class to use based on the current user's access
        serializer_class = RepositoryApproveSerializer
        if request.user in repo.admins.all():
            serializer_class = self.get_serializer_class()

        serializer = serializer_class(repo, context=self.get_serializer_context())
        return Response(serializer.data)


################################################################################
# Views
################################################################################

class MeView(APIView):
    def get(self, request, format=None):
        if not request.user.is_authenticated():
            resp = {
                'is_authenticated': False,
            }
        else:
            resp = {
                'repositories': RepositoryViewSet.as_view({'get': 'list'})(request).data,
                'username': request.user.username,
                'is_authenticated': True,
                'urls': {
                    'logout': reverse('account_logout', request=request),
                },
            }
        return Response(resp)


################################################################################
# Router
################################################################################

router = routers.DefaultRouter()

router.register('email-map', EmailMapViewSet)
router.register('repository', RepositoryViewSet)

urlpatterns = [
    url(r'^me/$', MeView.as_view(), name='fb-github-me'),
    url(r'^', include(router.urls)),
]
