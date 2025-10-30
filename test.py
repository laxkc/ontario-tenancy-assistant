from abc import ABC, abstractmethod

class BaseModel:
    def save(self):
        print("Saved to database")

class User(BaseModel):
    def __init__(self, name, email):
        self.name = name
        self.email = email
    
    def save(self):
        print(f"Saving user {self.name} to database")
        super().save()



class Math:
    @staticmethod
    def add(a, b):
        return a + b


class Logger:
    def log(self, message):
        print(f"Logging: {message}")

class UserService:
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def create_user(self, name, email):
        self.logger.log(f"Creating user {name} with email {email}")
        user = User(name, email)
        user.save()

# logger = Logger()
# user_service = UserService(logger)
# user_service.create_user("John Doe", "john.doe@example.com")


class Animal(ABC):
    @abstractmethod
    def make_sound(self):
        pass

class Dog(Animal):
    def make_sound(self):
        print("Woof")

class Cat(Animal):
    def make_sound(self):
        print("Meow")

# animals = [Dog(), Cat()]
# for animal in animals:
#     animal.make_sound()


def add(a, b):
    return a + b

def add_decorator(func):
    def wrapper(a, b):
        return func(a, b)
    return wrapper


@add_decorator
def add(a, b):
    print("Adding two numbers 2")
    return a + b

print(add(1, 2))
