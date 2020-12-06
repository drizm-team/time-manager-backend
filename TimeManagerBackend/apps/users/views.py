import logging

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
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

from TimeManagerBackend.lib.gcp_auth import (
    IsServiceAccount,
    ServiceAccountIDTokenAuthStrictWhenLive
)
from TimeManagerBackend.lib.viewsets import PatchUpdateModelViewSet
from .models import serializers
from .models.serializers import (
    UserSerializer,
    PasswordChangeSerializer,
    EmailChangeSerializer
)


@swagger_auto_schema(
    method="post",
    auto_schema=None  # noqa expected type
)
@api_view(["POST"])
@authentication_classes([ServiceAccountIDTokenAuthStrictWhenLive])
@permission_classes([IsServiceAccount])
def __manage_flush_expired__(request: Request, *args, **kwargs) -> Response:
    """ Endpoint for the flushexpiredtokens management task invocation """
    logger = logging.getLogger("cloud")
    logger.warning("Management Endpoint invoked")

    call_command("flushexpiredtokens")
    # we need to include *some* content or Google will flag it as a 400 or 500
    return Response({"status": "OK"}, status=status.HTTP_200_OK)


@method_decorator(
    name="create", decorator=swagger_auto_schema(
        operation_summary="Create User",
        security=[],
    )
)
@method_decorator(
    name="retrieve", decorator=swagger_auto_schema(
        operation_summary="Retrieve singular User",
    )
)
@method_decorator(
    name="list", decorator=swagger_auto_schema(
        operation_summary="List all visible Users",
    )
)
@method_decorator(
    name="destroy", decorator=swagger_auto_schema(
        operation_summary="Delete User",
    )
)
class UserViewSet(PatchUpdateModelViewSet):
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

    def partial_update(self, request, *args, **kwargs):
        if "password" in request.data:
            return Response(
                "Password can only be changed from the change_password endpoint.",
                status=status.HTTP_400_BAD_REQUEST
            )

        if "email" in request.data:
            return Response(
                "Email can only be changed from the change_email endpoint.",
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        method="patch",
        operation_summary="Change Password",
        request_body=PasswordChangeSerializer,
        responses={
            status.HTTP_205_RESET_CONTENT: "Operation Successful",
            status.HTTP_403_FORBIDDEN: "Not allowed to perform this operation"
                                       "on the requested user"
        }
    )
    @action(
        methods=["PATCH"],
        url_path="change-password",
        detail=True
    )
    def change_password(self, request, *args, **kwargs):
        requested_user = get_object_or_404(
            self.get_queryset(), pk=kwargs.get("pk")
        )
        requesting_user = request.user
        if not requested_user == requesting_user:
            raise PermissionDenied

        # make sure that the request payload is valid
        serializer = PasswordChangeSerializer(
            requested_user,
            data=request.data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # find all refresh tokens of the user and blacklist them
        try:
            tokens = OutstandingToken.objects.filter(
                user=requested_user, blacklistedtoken__isnull=True
            )
            for token in tokens:
                token = RefreshToken(token.token)
                token.blacklist()
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(status=status.HTTP_205_RESET_CONTENT)

    @swagger_auto_schema(
        method="patch",
        operation_summary="Change Email",
        request_body=EmailChangeSerializer,
        responses={
            status.HTTP_200_OK: UserSerializer(),
            status.HTTP_403_FORBIDDEN: "Not allowed to perform this operation"
                                       "on the requested user"
        }
    )
    @action(
        methods=["PATCH"],
        url_path="change-email",
        detail=True
    )
    def change_email(self, request, *args, **kwargs):
        requested_user = get_object_or_404(
            self.get_queryset(), pk=kwargs.get("pk")
        )
        requesting_user = request.user
        if not requested_user == requesting_user:
            raise PermissionDenied

        serializer = EmailChangeSerializer(
            requested_user,
            data=request.data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user_serializer = UserSerializer(
            requested_user,
            context=self.get_serializer_context()
        )
        return Response(
            user_serializer.data,
            status=status.HTTP_200_OK
        )
