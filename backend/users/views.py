from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.pagination import CustomPagination
from .serializers import FollowSerializer
from users.models import Follow
from users.serializers import FollowCreateSerializer

BaseUser = get_user_model()


class CustomUserViewSet(UserViewSet):
    pagination_class = CustomPagination

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(BaseUser, pk=id)

        if request.method == "POST":
            serializer = FollowCreateSerializer(
                data={"author": author.pk},
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            return Response(
                FollowSerializer(
                    instance,
                    context={"request": request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        subscription = Follow.objects.filter(user=request.user, author=author)
        if subscription.count() != 0:
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        queryset = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
