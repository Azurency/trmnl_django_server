import inspect


def get_full_class_path(cls):
    module = inspect.getmodule(cls)
    if module:
        module_name = module.__name__
    else:
        module_name = "__main__"
    class_name = cls.__name__
    return f"{module_name}.{class_name}"
