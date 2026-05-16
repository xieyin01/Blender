from .collection_operators import (
    CollectObjectOperator,
    AddCollectionDirectOperator,
    RemoveCollectionOperator,
    RenameCollectionDirectOperator,
    SelectAllCollectedOperator,
    RemoveCollectedObjectOperator,
    SelectCollectionByClickOperator,
    register_operators,
    unregister_operators
)

__all__ = [
    'CollectObjectOperator',
    'AddCollectionDirectOperator',
    'RemoveCollectionOperator',
    'RenameCollectionDirectOperator',
    'SelectAllCollectedOperator',
    'RemoveCollectedObjectOperator',
    'SelectCollectionByClickOperator',
    'register_operators',
    'unregister_operators',
]