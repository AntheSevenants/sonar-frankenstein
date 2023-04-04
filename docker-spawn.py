import argparse
import subprocess

#
# Argument parsing
#

parser = argparse.ArgumentParser(
    description='docker-spawn - spawn a bunch of Alpino parsers')
parser.add_argument('command', type=str,
                    help='run | start | stop | rm')
parser.add_argument('alpino_count', type=int, nargs='?',
                    default=8, help='Name of the output file')

args = parser.parse_args()

if not args.command in ["run", "start", "stop", "rm"]:
    raise ValueError("Unrecognised command")

# This is the base port for our Alpino
# Each instance will be opened at BASE_PORT + n 
# with n = the id of the Alpino instance
BASE_PORT = 7000

for alpino_id in list(range(1, args.alpino_count + 1)):
    container_name = f"alpino-server-{alpino_id}"
    port = BASE_PORT + alpino_id

    if args.command == "run":
        # Spawn the Docker container
        arguments = ["docker", "run", "-d", "-p", f"{port}:7001", "--name", container_name, "anthesevenants/alpino-server"]
    elif args.command == "start":
        # Start existing Docker containers
        arguments = ["docker", "start", container_name]
    elif args.command == "stop":
        # Stop existing Docker containers
        arguments = ["docker", "stop", container_name]
    elif args.command == "rm":
        # Stop existing Docker containers
        arguments = ["docker", "rm", container_name]

    subprocess.run(arguments)