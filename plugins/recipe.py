class BaseRecipe:
    def __init__(self, config):
        self.config = config

    def generate_html(self):
        raise NotImplementedError

    def __str__(self):
        return f"<Recipe {self.__class__.__name__}>"


class StaticHTMLRecipe(BaseRecipe):
    def generate_html(self):
        return self.config["html"]
