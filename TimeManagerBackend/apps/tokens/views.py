from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, permissions
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView as __TokenObtainPairView,
    TokenRefreshView as __TokenRefreshView,
    TokenVerifyView as __TokenVerifyView,
)

from .serializers import (
    CustomTokenObtainPairSerializer,
    ObtainSchema,
    RefreshSchema,
    TokenDestroySchema
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

    @swagger_auto_schema(
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
    @permission_classes([permissions.AllowAny])
    def delete(self, request, *args, **kwargs):
        serializer = TokenDestroySchema(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data.get("refresh"))
            token.blacklist()
        except TokenError as e:
            raise InvalidToken(e.args[0])
        return Response(status=status.HTTP_205_RESET_CONTENT)


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
