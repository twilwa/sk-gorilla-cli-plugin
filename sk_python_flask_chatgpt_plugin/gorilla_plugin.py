import subprocess
import os
from typing import List, Dict
import sys


class GorillaPlugin:
    _cli_path: str
    _env_info: Dict[str, str]
    _working_directory: str = None

    """A plugin that uses the Gorilla CLI to perform a series of executions based on a natural language query or high level overview of the user's problem."""

    def set_working_directory(self, directory: str) -> None:
        """
        Sets the working directory for the environment.
        """
        self._working_directory = directory

    def collect_environment_info(self) -> None:
        """
        Collects information about the environment where the commands are executed, including the file structure.
        """
        self._env_info = {}
        if self._working_directory:
            try:
                for root, dirs, files in os.walk(self._working_directory):
                    self._env_info[root] = dirs + files
            except Exception as e:
                self._env_info[
                    "error"
                ] = f"Exception collecting file structure: {str(e)}"

    def compare_environment_info(
        self, initial_env_info: Dict[str, str], updated_env_info: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Compares the initial and updated environment information and returns the differences.
        """
        return {
            key: {
                "initial": initial_env_info[key],
                "updated": updated_env_info.get(key),
            }
            for key, value in initial_env_info.items()
            if value != updated_env_info.get(key)
        }

    def queue_commands(self, natural_language_commands: List[str]) -> List[str]:
        """
        Processes natural language commands and queues them for execution after user confirmation.
        """
        queued_commands = []
        for nl_command in natural_language_commands:
            # Pass the natural language command to the Gorilla CLI and get the CLI command
            try:
                process = subprocess.Popen(
                    f'{self._cli_path} "{nl_command}"',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                stdout, stderr = process.communicate()

                if process.returncode != 0:
                    print(f"Failed to get CLI command for: {nl_command}")
                    print(f"Error: {stderr.decode().strip()}")
                    continue
            except Exception as e:
                print(f"Exception while processing command '{nl_command}': {str(e)}")
                continue

            cli_command = stdout.decode().strip()
            queued_commands.append(cli_command)
        # Option to dump commands to a script instead of executing
        self.dump_commands_to_script(queued_commands)

        # Return both the queued commands and the environment information
        return {"queued_commands": queued_commands, "environment_info": self._env_info}

    def dump_commands_to_script(
        self, cli_commands: List[str], filename: str = "gorilla_commands"
    ) -> None:
        """
        Dumps the queued CLI commands into a script file.
        """
        # Determine the script file extension based on the operating system
        script_extension = "sh" if os.name == "posix" else "bat"
        full_filename = f"{filename}.{script_extension}"

        # Write the commands to the script file
        with open(full_filename, "w") as script_file:
            if script_extension == "sh":
                script_file.write("#!/bin/sh\n\n")
            for command in cli_commands:
                script_file.write(f"{command}\n")
            if script_extension == "bat":
                script_file.write("pause\n")

        print(f"Commands dumped to script: {full_filename}")

    def execute_commands(self, cli_commands: List[str]):
        """
        Executes a list of CLI commands after user confirmation.
        """
        # Ask for user confirmation before executing commands
        user_confirmation = input(
            "Do you want to execute the queued commands? (yes/no): "
        )
        if user_confirmation.lower() != "yes":
            print("Execution cancelled by the user.")
            return

        # Collect initial environment info
        self.collect_environment_info()
        initial_env_info = self._env_info.copy()

        for cli_command in cli_commands:
            # Execute the CLI command using subprocess
            process = subprocess.Popen(
                cli_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                print(f"Command executed successfully: {cli_command}")
                print(f"Output: {stdout.decode().strip()}")
            else:
                print(f"Command failed: {cli_command}")
                print(f"Error: {stderr.decode().strip()}")

            # Collect updated environment info
            self.collect_environment_info()
            updated_env_info = self._env_info.copy()

            if env_changes := self.compare_environment_info(
                initial_env_info, updated_env_info
            ):
                print("Environment changes detected:")
                for key, change in env_changes.items():
                    print(f"{key}: from '{change['initial']}' to '{change['updated']}'")


def confirm_and_execute_commands(
    gorilla_plugin: GorillaPlugin, queued_commands: List[str]
):
    """
    Confirms with the user before executing queued commands.
    """
    # Ask for user confirmation before executing commands
    user_confirmation = input("Do you want to execute the queued commands? (yes/no): ")
    if user_confirmation.lower() != "yes":
        print("Execution cancelled by the user.")
        return

    # If confirmed, execute the commands
    gorilla_plugin.execute_commands(queued_commands)


def main(argv):
    # Get user input and API endpoint URL from command-line arguments
    if len(argv) < 3:
        print("Usage: python gorilla_plugin.py '<command>' '<api_endpoint_url>'")
        return
    user_input = argv[1]
    argv[2]

    # Initialize GorillaPlugin with the path to the Gorilla CLI
    import os

    gorilla_plugin = GorillaPlugin(cli_path=os.getenv("GORILLA_CLI_PATH"))

    # Process the input and queue CLI commands
    queued_commands = gorilla_plugin.queue_commands([user_input])

    # Confirm and execute commands
    confirm_and_execute_commands(gorilla_plugin, queued_commands)


if __name__ == "__main__":
    main(sys.argv)
