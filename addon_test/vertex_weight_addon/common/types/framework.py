import bpy


def is_extension():
    return str(__package__).startswith("bl_ext.")


class ExpandableUi:
    target_id: str
    expand_mode: str = "APPEND"

    def draw(self, context: bpy.types.Context):
        raise NotImplementedError("draw method must be implemented")


def reg_order(order_value: int):
    def class_decorator(cls):
        cls._reg_order = order_value
        return cls
    return class_decorator
