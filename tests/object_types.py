"""DjangoObjectType classes."""

import graphene
from graphene_django import DjangoObjectType

from .filter_sets import TaskFilter, TaskGroupFilter, UserFilter
from .models import Task, TaskGroup, User


class UserFilterFieldsType(DjangoObjectType):
    """UserType with the `filter_fields` field in the Meta class."""

    class Meta:
        model = User
        interfaces = (graphene.relay.Node,)
        fields = '__all__'
        filter_fields = {
            'first_name': ('exact', 'startswith'),
            'last_name': ('exact', 'contains'),
            'email': ('exact',),
            'is_active': ('exact',),
            'birthday': ('exact',),
        }


class UserFilterSetClassType(DjangoObjectType):
    """UserType with the `filterset_class` field in the Meta class."""

    class Meta:
        model = User
        interfaces = (graphene.relay.Node,)
        fields = '__all__'
        filterset_class = UserFilter


class TaskFilterFieldsType(DjangoObjectType):
    """TaskType with the `filter_fields` field in the Meta class."""

    user = graphene.Field(UserFilterFieldsType, description='User field')

    class Meta:
        model = Task
        interfaces = (graphene.relay.Node,)
        fields = '__all__'
        filter_fields = {
            'name': ('exact',),
            'created_at': ('exact', 'gt'),
            'completed_at': ('lt',),
            'user__email': ('exact', 'iexact', 'contains', 'icontains'),
        }


class TaskFilterSetClassType(DjangoObjectType):
    """TaskType with the `filterset_class` field in the Meta class."""

    user = graphene.Field(UserFilterSetClassType, description='User field')

    class Meta:
        model = Task
        interfaces = (graphene.relay.Node,)
        fields = ('name', 'user')
        filterset_class = TaskFilter


class TaskGroupFilterFieldsType(DjangoObjectType):
    """TaskGroupType with the `filter_fields` field in the Meta class."""

    tasks = graphene.List(graphene.NonNull(TaskFilterFieldsType), description='Tasks field')

    class Meta:
        model = TaskGroup
        interfaces = (graphene.relay.Node,)
        fields = '__all__'
        filter_fields = {
            'name': ('exact', 'contains'),
            'priority': ('exact', 'gte'),
            'tasks': ('exact',),
        }


class TaskGroupFilterSetClassType(DjangoObjectType):
    """TaskGroupType with the `filterset_class` field in the Meta class."""

    tasks = graphene.List(graphene.NonNull(TaskFilterSetClassType), description='Tasks field')

    class Meta:
        model = TaskGroup
        interfaces = (graphene.relay.Node,)
        fields = '__all__'
        filterset_class = TaskGroupFilter