import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.presentation.runner.application_runner import ApplicationRunner

def main():
    ApplicationRunner().run()

if __name__ == "__main__":
    main()
