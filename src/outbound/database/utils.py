from sqlalchemy import Enum


def pg_enum(enum_cls: type) -> Enum:
    return Enum(
        enum_cls,
        native_enum=True,
        values_callable=lambda x: [e.value for e in x],
    )
