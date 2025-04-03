"""`AdvancedDjangoFilterConnectionField` class module.

Use the `AdvancedDjangoFilterConnectionField` class from this
module instead of the `DjangoFilterConnectionField` from graphene-django.
"""

import warnings
from typing import Any, Callable, Dict, Iterable, Optional, Type, Union

import graphene
from django.core.exceptions import ValidationError
from django.db import models
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphene.utils.str_converters import to_snake_case

from .conf import settings
from .filter_arguments_factory import FilterArgumentsFactory
from .filterset import AdvancedFilterSet
from .filterset_factories import get_filterset_class
from .input_data_factories import tree_input_type_to_data


class AdvancedDjangoFilterConnectionField(DjangoFilterConnectionField):
    """Allow you to use advanced filters provided by this library."""

    def __init__(
        self,
        type: Union[Type[DjangoObjectType], Callable[[], Type[DjangoObjectType]], str],
        fields: Optional[Dict[str, list]] = None,
        order_by: Any = None,
        extra_filter_meta: Optional[dict] = None,
        filterset_class: Optional[Type[AdvancedFilterSet]] = None,
        filter_input_type_prefix: Optional[str] = None,
        *args,
        **kwargs
    ) -> None:
        super().__init__(
            type,
            fields,
            order_by,
            extra_filter_meta,
            filterset_class,
            *args,
            **kwargs
        )
        assert self.provided_filterset_class is None or issubclass(
            self.provided_filterset_class, AdvancedFilterSet,
        ), 'Use the `AdvancedFilterSet` class with the `AdvancedDjangoFilterConnectionField`'
        self._filter_input_type_prefix = filter_input_type_prefix
        if self._filter_input_type_prefix is None and self._provided_filterset_class:
            warnings.warn(
                'The `filterset_class` argument without `filter_input_type_prefix` '
                'can result in different types with the same name in the schema.',
            )
        if self._filter_input_type_prefix is None and self.node_type._meta.filterset_class:
            warnings.warn(
                f'The `filterset_class` field of `{self.node_type.__name__}` Meta '
                'without the `filter_input_type_prefix` argument '
                'can result in different types with the same name in the schema.',
            )

    @property
    def provided_filterset_class(self) -> Optional[Type[AdvancedFilterSet]]:
        """Return a provided AdvancedFilterSet class."""
        return self._provided_filterset_class or self.node_type._meta.filterset_class

    @property
    def filter_input_type_prefix(self) -> str:
        """Return a prefix for a filter input type name."""
        if self._filter_input_type_prefix:
            return self._filter_input_type_prefix
        node_type_name = self.node_type.__name__.replace('Type', '')
        if self.provided_filterset_class:
            return f'{node_type_name}{self.provided_filterset_class.__name__}'
        else:
            return node_type_name

    @property
    def filterset_class(self) -> Type[AdvancedFilterSet]:
        """Return a AdvancedFilterSet instead of a FilterSet."""
        if not self._filterset_class:
            fields = self._fields or self.node_type._meta.filter_fields
            meta = {'model': self.model, 'fields': fields}
            if self._extra_filter_meta:
                meta.update(self._extra_filter_meta)
            self._filterset_class = get_filterset_class(self.provided_filterset_class, **meta)
        return self._filterset_class

    @property
    def filtering_args(self) -> dict:
        """Return filtering args from the filterset."""
        if not self._filtering_args:
            self._filtering_args = FilterArgumentsFactory(
                self.filterset_class,
                self.filter_input_type_prefix,
            ).arguments
        return self._filtering_args

    @classmethod
    def resolve_queryset(
        cls,
        connection: object,
        iterable: Iterable,
        info: graphene.ResolveInfo,
        args: Dict[str, Any],
        filtering_args: Dict[str, graphene.InputField],
        filterset_class: Type[AdvancedFilterSet],
    ) -> models.QuerySet:
        """Return a filtered QuerySet."""
        qs = super(DjangoFilterConnectionField, cls).resolve_queryset(
            connection, iterable, info, args,
        )

        order = args.get("orderBy", None)
        if order:
            if isinstance(order, str):
                snake_order = to_snake_case(order)
            else:
                snake_order = [to_snake_case(o) for o in order]

            # annotate counts for ordering
            for order_arg in snake_order:
                order_arg = order_arg.lstrip("-")
                annotation_name = f"annotate_{order_arg}"
                annotation_method = getattr(qs, annotation_name, None)
                if annotation_method:
                    qs = annotation_method()

            # override the default distinct parameters
            # as they might differ from the order_by params
            qs = qs.order_by(*snake_order).distinct()

        filter_arg = args.get(settings.FILTER_KEY, {})
        filterset = filterset_class(
            data=tree_input_type_to_data(filterset_class, filter_arg),
            queryset=qs,
            request=info.context,
        )
        if filterset.form.is_valid():
            return filterset.qs
        raise ValidationError(filterset.form.errors.as_json())
