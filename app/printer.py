from termcolor import colored

class Printer:
    
    @staticmethod
    def print_red(msg: str) -> None:
        print(colored(msg, color="red"))
        
    @staticmethod
    def print_green(msg: str) -> None:
        print(colored(msg, color='green'))
        
    @staticmethod
    def print_blue(msg: str) -> None:
        print(colored(msg, 'blue'))
  