from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenObtainPairView as __TokenObtainPairView,
    TokenRefreshView as __TokenRefreshView,
    TokenVerifyView as __TokenVerifyView,
)

from .models import serializers
from .models.serializers import (
    CustomTokenObtainPairSerializer,
    ObtainSchema,
    RefreshSchema,
    UserResponseSchema
)


@method_decorator(
    name="post", decorator=swagger_auto_schema(
        operation_summary="Create Token",
        operation_description="Takes a set of user credentials "
                              "and returns an access and refresh JSON web"
                              "token pair to prove the authentication of "
                              "those credentials.",
        security=[],
        responses={
            status.HTTP_200_OK: ObtainSchema(),
            status.HTTP_401_UNAUTHORIZED: "Invalid Credentials"
        }
    )
)
class TokenObtainPairView(__TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@method_decorator(
    name="post", decorator=swagger_auto_schema(
        operation_summary="Request new Token",
        operation_description="Takes a refresh type JSON web token "
                              "and returns an access type JSON web token "
                              "if the refresh token is valid.",
        security=[],
        responses={
            status.HTTP_200_OK: RefreshSchema(),
            status.HTTP_401_UNAUTHORIZED: "Refresh token invalid"
        }
    )
)
class TokenRefreshView(__TokenRefreshView):
    pass


@method_decorator(
    name="post", decorator=swagger_auto_schema(
        operation_summary="Verify Token",
        operation_description="Takes a token and indicates if it is valid."
                              " This view provides no information "
                              "about a token's fitness for a particular use.",
        security=[],
        responses={
            status.HTTP_200_OK: "Access token valid",
            status.HTTP_401_UNAUTHORIZED: "Access token invalid"
        }
    )
)
class TokenVerifyView(__TokenVerifyView):
    pass


@method_decorator(
    name="create", decorator=swagger_auto_schema(
        operation_summary="Create User",
        security=[],
        responses={
            status.HTTP_200_OK: UserResponseSchema(),
            status.HTTP_400_BAD_REQUEST: "Validation failed"
        }
    )
)
@method_decorator(
    name="retrieve", decorator=swagger_auto_schema(
        operation_summary="Retrieve singular User",
        responses={
            status.HTTP_200_OK: UserResponseSchema(),
            status.HTTP_404_NOT_FOUND: "Specified ID does not match a user"
        }
    )
)
@method_decorator(
    name="list", decorator=swagger_auto_schema(
        operation_summary="List all visible Users",
        responses={
            status.HTTP_200_OK: UserResponseSchema(many=True)
        }
    )
)
@method_decorator(
    name="destroy", decorator=swagger_auto_schema(
        operation_summary="Delete User",
    )
)
class UserViewSet(viewsets.GenericViewSet,
                  mixins.CreateModelMixin,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.DestroyModelMixin):
    serializer_class = serializers.UserSerializer

    def get_queryset(self):
        User = get_user_model()
        return User.objects.filter(id=self.request.user.id).all()

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(
        operation_summary="Update User",
        responses={
            status.HTTP_200_OK: UserResponseSchema(),
            status.HTTP_400_BAD_REQUEST: "Validation failed"
        }
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


user_viewset_list = UserViewSet.as_view({
    "get": "list",
    "post": "create"
})
user_viewset_detail = UserViewSet.as_view({
    "get": "retrieve",
    "patch": "update",
    "delete": "destroy"
})
