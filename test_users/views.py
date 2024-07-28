from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
import environ

from .models import User
from .serializers import UserSerializer

# чтение значений из файла .env, в котором хранятся настройки базы данных
env = environ.Env()
environ.Env.read_env()

# создадим переменную use_db, определяющую будет ли использована баща данных, или репозиторий будет храниться в памяти
# если значение DB_TYPE в файле .env содержит строку "memory", репозиторий хранится в памяти,
# в другом случае используется база данных, указанная в файле .env
use_db = False if env('DB_TYPE') == 'memory' else True

# в случае, если применяется база данных, создадим класс viewset для работы с объектом user
if use_db:
    class UserViewSet(viewsets.ViewSet):
        def list(self, request):
            # получение списка пользователей
            queryset = User.objects.all()
            serializer = UserSerializer(queryset, many=True)
            return Response(serializer.data)

        def retrieve(self, request, pk=None):
            # получение информации о пользователе
            queryset = User.objects.all()
            user = get_object_or_404(queryset, pk=pk)
            serializer = UserSerializer(user)
            return Response(serializer.data)

        def create(self, request):
            # создание пользователя
            serializer = UserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'User created': serializer.data}, status=status.HTTP_201_CREATED)

        def update(self, request, *args, **kwargs):
            # обновление информации о пользователе
            pk = kwargs.get("pk", None)
            if not pk:
                return Response({"error": "Method PUT not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
            try:
                instance = User.objects.get(pk=pk)
            except:
                return Response({"error": "Object does not exists"}, status=status.HTTP_404_NOT_FOUND)
            serializer = UserSerializer(data=request.data, instance=instance)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'User updated': serializer.data}, status=status.HTTP_201_CREATED)

        def destroy(self, request, *args, **kwargs):
            pk = kwargs.get("pk", None)
            if not pk:
                return Response({"error": "Method DELETE not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
            try:
                User.objects.filter(pk=pk).delete()
            except:
                return Response({"error": "Object does not exists"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"User deleted": str(pk)})

# в случае реализации репозитория в памяти, создадим класс, хранящий объекты user
else:
    class UserRepository:
        users = {}
        next_id = 1

        def create_user(self, full_name):
            user = User(id=self.next_id, full_name=full_name)
            self.users[self.next_id] = user
            self.next_id += 1
            return user

        def get_user(self, user_id):
            return self.users.get(user_id)

        def update_user(self, user_id, full_name):
            if user_id in self.users:
                self.users[user_id].full_name = full_name
                return self.users[user_id]
            return None

        def delete_user(self, user_id):
            if user_id in self.users:
                return self.users.pop(user_id)
            return None

    # создадим экземпляр класса
    repository = UserRepository()

    # создадим viewset, с учетом реализации репозитория в памяти,
    # вероятно, здесь, вместо создания двух похожих классов viewset, можно создать родительский класс и два наследующих
    class UserViewSet(viewsets.ViewSet):
        def list(self, request):
            # получение списка пользователей
            queryset = repository.users.values()
            serializer = UserSerializer(queryset, many=True)
            return Response(serializer.data)

        def retrieve(self, request, pk=None):
            # получение информации о пользователе
            user = repository.get_user(int(pk))
            if user:
                serializer = UserSerializer(user)
                return Response(serializer.data)
            return Response({"error": "Object does not exists"}, status=status.HTTP_404_NOT_FOUND)

        def create(self, request):
            # создание пользователя
            serializer = UserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = repository.create_user(request.data.get('full_name'))
            return Response({'User created': {'id': user.id, 'full_name': user.full_name}},
                            status=status.HTTP_201_CREATED)

        def update(self, request, *args, **kwargs):
            # обновление информации о пользователе
            pk = kwargs.get("pk", None)
            if not pk:
                return Response({"error": "Method PUT not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

            serializer = UserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = repository.update_user(int(pk), request.data.get('full_name'))
            if user:
                return Response({'User updated': {'id': user.id, 'full_name': user.full_name}},
                                status=status.HTTP_201_CREATED)
            return Response({"error": "Object does not exists"}, status=status.HTTP_404_NOT_FOUND)

        def destroy(self, request, *args, **kwargs):
            # удаление пользователя
            pk = kwargs.get("pk", None)
            if not pk:
                return Response({"error": "Method DELETE not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
            user = repository.delete_user(int(pk))
            if user:
                return Response({"User deleted": str(pk)})
            return Response({"error": "Object does not exists"}, status=status.HTTP_404_NOT_FOUND)
