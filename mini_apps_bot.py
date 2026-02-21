# mini_apps_bot.py

class MiniAppsBot:
    def __init__(self):
        print("Mini Apps Bot Initialized!")

    def run(self):
        print("Running the Mini Apps Bot...")
        while True:
            command = input("Enter a command (type 'exit' to quit): ")
            if command.lower() == 'exit':
                print("Exiting Mini Apps Bot...")
                break
            self.handle_command(command)

    def handle_command(self, command):
        if command == "hello":
            print("Hello! How can I assist you?")
        elif command == "calc":
            self.calculator()
        else:
            print(f"Unknown command: {command}")

    def calculator(self):
        print("Simple Calculator. Type 'exit' to quit.")
        while True:
            expression = input("Enter expression (e.g., 2 + 2): ")
            if expression.lower() == 'exit':
                break
            try:
                result = eval(expression)
                print(f"Result: {result}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    bot = MiniAppsBot()
    bot.run()