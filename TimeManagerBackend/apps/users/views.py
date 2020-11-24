import json
import logging

import google.auth.transport.requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.management import call_command
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from drizm_commons.utils import Path
from google.oauth2 import id_token
from rest_framework import permissions, status
from rest_framework import viewsets, mixins
from rest_framework.decorators import (
    action,
    api_view,
    permission_classes,
    authentication_classes
)
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
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
    UserResponseSchema,
    PasswordChangeSerializer,
    UserSerializer,
    TokenDestroySchema
)
from ..errors.errors import PasswordMismatchException


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


@swagger_auto_schema(
    method="post",
    operation_summary="Delete Token",
    operation_description="Destroys or deletes a token. "
                          "May be used to facilitate logout behaviour.",
    request_body=TokenDestroySchema,
    responses={
        status.HTTP_205_RESET_CONTENT: "Operation Successful",
        status.HTTP_401_UNAUTHORIZED: "Refresh token invalid"
    },
    security=[]
)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def token_destroy_view(request, *args, **kwargs):
    serializer = TokenDestroySchema(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        token = RefreshToken(serializer.validated_data.get("refresh"))
        token.blacklist()
    except TokenError as e:
        raise InvalidToken(e.args[0])
    return Response(status=status.HTTP_205_RESET_CONTENT)


@swagger_auto_schema(method="post", auto_schema=None)
@api_view(["POST"])
@permission_classes([])
@authentication_classes([])
def __manage_flush_expired__(request: Request, *args, **kwargs) -> Response:
    """ Endpoint for the flushexpiredtokens management task invocation """
    logger = logging.getLogger("cloud")
    logger.warning(request.META)
    logger.warning("Management Endpoint invoked")
    auth = request.META.get("HTTP_AUTHORIZATION").split()
    if auth[0] != "Bearer":
        return Response(
            {"status": "Bad Auth Scheme"},
            status=status.HTTP_400_BAD_REQUEST
        )
    token = auth[1]

    try:
        req = google.auth.transport.requests.Request()
        payload = id_token.verify_token(
            token, request=req
        )
        logger.warning(payload)
    except Exception:  # noqa E722
        return Response(
            {"status": "Bad Token Scheme"},
            status=status.HTTP_400_BAD_REQUEST
        )

    authorized_service_account = settings.GS_CREDENTIALS
    with open(Path(settings.GS_CREDENTIALS_FILE), "r") as fin:
        content = json.load(fin)
    if (
        not payload.get("iss") == "https://accounts.google.com"
        or not payload.get("email") == authorized_service_account.service_account_email
        or not payload.get("email_verified", False)
        or not payload.get("sub") == content.get("client_id")
    ):
        return Response(
            {"status": "Bad Token Scheme"},
            status=status.HTTP_400_BAD_REQUEST
        )

    call_command("flushexpiredtokens")
    # we need to include *some* content or Google will flag it as a 400 or 500
    return Response({"status": "OK"}, status=status.HTTP_200_OK)


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
            permission_classes_ = [permissions.AllowAny]
        else:
            permission_classes_ = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes_]

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

    @swagger_auto_schema(
        method="post",
        operation_summary="Change Password",
        request_body=PasswordChangeSerializer,
        responses={
            status.HTTP_205_RESET_CONTENT: "Operation Successful",
            status.HTTP_403_FORBIDDEN: "Not allowed to perform this operation"
                                       "on the requested user"
        }
    )
    @action(methods=["post"], url_path="change-password", detail=True)
    def change_password(self, request, *args, **kwargs):
        requested_user = get_object_or_404(
            self.get_queryset(), pk=kwargs.get("pk")
        )
        requesting_user = request.user
        if not requested_user == requesting_user:
            raise PermissionDenied

        # make sure that the request payload is valid
        serializer = PasswordChangeSerializer(
            data=request.data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)

        # check that the old_password is identical to the stored one
        if not check_password(
                serializer.validated_data.get("old_password"),
                requesting_user.password
        ):
            raise PasswordMismatchException

        # change the password
        user_serializer = UserSerializer(
            requesting_user,
            data={
                "password": serializer.validated_data.get("new_password")
            },
            partial=True
        )
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        # find all refresh tokens of the user and blacklist them
        try:
            tokens = OutstandingToken.objects.filter(
                user=requesting_user, blacklistedtoken__isnull=True
            )
            for token in tokens:
                token = RefreshToken(token.token)
                token.blacklist()
        except TokenError as e:
            raise InvalidToken(e.args[0])
        return Response(status=status.HTTP_205_RESET_CONTENT)


user_viewset_list = UserViewSet.as_view({
    "get": "list",
    "post": "create"
})
user_viewset_detail = UserViewSet.as_view({
    "get": "retrieve",
    "patch": "update",
    "delete": "destroy"
})
user_viewset_change_password = UserViewSet.as_view({
    "post": "change_password"
})
