import asyncio
import logging

from app.db import BotUser


async def docker_build_and_run(user: BotUser) -> tuple[bool, str]:
    """
    Builds and runs a Docker image for the given user.
    Returns True if successful, False otherwise.
    """
    build_image_cmd = f"docker build -t tg-bot-forwarder-{user.id} ../tg_bot_forwarder"
    run_image_cmd = (
        f"docker run -d --restart=on-failure:2 --env-file ../tg_bot_forwarder/.env "
        f"-e USER_ID={user.id} "
        f"--name tg-bot-forwarder-{user.id} tg-bot-forwarder-{user.id}"
    )
    # 1) Docker BUILD
    try:
        logging.info(f"[Docker] Building image with: {build_image_cmd}")
        build_proc = await asyncio.create_subprocess_shell(
            build_image_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        build_stdout, build_stderr = await build_proc.communicate()

        if build_proc.returncode != 0:
            logging.error(
                f"[Docker] BUILD failed with return code {build_proc.returncode}\n"
                f"STDOUT: {build_stdout.decode().strip()}\n"
                f"STDERR: {build_stderr.decode().strip()}"
            )
            build_message = (f"Build image failed!, code: {build_proc.returncode}, stdout: {build_stdout.decode()}, "
                             f"stderr: {build_stderr.decode()}")
            return False, build_message
        else:
            logging.info(
                f"[Docker] BUILD succeeded.\n"
                f"STDOUT: {build_stdout.decode().strip()}\n"
                f"STDERR: {build_stderr.decode().strip()}"
            )
    except Exception as e:
        logging.error(f"[Docker] Exception during build: {e}", exc_info=True)
        build_message = f"Exception during build image: {e}"
        return False, build_message

    # 2) Docker RUN
    try:
        logging.info(f"[Docker] Running container with: {run_image_cmd}")
        run_proc = await asyncio.create_subprocess_shell(
            run_image_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        run_stdout, run_stderr = await run_proc.communicate()

        if run_proc.returncode != 0:
            logging.error(
                f"[Docker] RUN failed with return code {run_proc.returncode}\n"
                f"STDOUT: {run_stdout.decode().strip()}\n"
                f"STDERR: {run_stderr.decode().strip()}"
            )
            rum_message = (f"Run container failed!, code: {run_proc.returncode}, "
                           f"stdout: {run_stdout.decode()}, stderr: {run_stderr.decode()}")
            return False, rum_message
        else:
            logging.info(
                f"[Docker] RUN succeeded.\n"
                f"STDOUT: {run_stdout.decode().strip()}\n"
                f"STDERR: {run_stderr.decode().strip()}"
            )
    except Exception as e:
        logging.error(f"[Docker] Exception during run: {e}", exc_info=True)
        run_message = f"Exception during run container: {e}"
        return False, run_message

    return True, f"Forwarder started successfully(user_id: {user.id})"


async def docker_restart(user: BotUser) -> tuple[bool, str]:
    restart_cmd = f"docker restart tg-bot-forwarder-{user.id}"
    try:
        logging.info(f"[Docker] Restarting container with: {restart_cmd}")
        restart_proc = await asyncio.create_subprocess_shell(
            restart_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        restart_stdout, restart_stderr = await restart_proc.communicate()

        if restart_proc.returncode != 0:
            logging.error(
                f"[Docker] RESTART failed with return code {restart_proc.returncode}\n"
                f"STDOUT: {restart_stdout.decode().strip()}\n"
                f"STDERR: {restart_stderr.decode().strip()}"
            )
            restart_message = (f"Restart container failed!, code: {restart_proc.returncode}, "
                               f"stdout: {restart_stdout.decode()}, stderr: {restart_stderr.decode()}")
            return False, restart_message
        else:
            logging.info(
                f"[Docker] RESTART succeeded.\n"
                f"STDOUT: {restart_stdout.decode().strip()}\n"
                f"STDERR: {restart_stderr.decode().strip()}"
            )
    except Exception as e:
        logging.error(f"[Docker] Exception during restart: {e}", exc_info=True)
        restart_message = f"Exception during restart container: {e}"
        return False, restart_message

    return True, f"Forwarder restarted successfully(user_id: {user.id})"


async def docker_stop_and_remove(user: BotUser) -> tuple[bool, str]:
    stop_cmd = f"docker stop tg-bot-forwarder-{user.id}"
    remove_cmd = f"docker rm tg-bot-forwarder-{user.id}"
    try:
        logging.info(f"[Docker] Stopping container with: {stop_cmd}")
        stop_proc = await asyncio.create_subprocess_shell(
            stop_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stop_stdout, stop_stderr = await stop_proc.communicate()

        if stop_proc.returncode != 0:
            logging.error(
                f"[Docker] STOP failed with return code {stop_proc.returncode}\n"
                f"STDOUT: {stop_stdout.decode().strip()}\n"
                f"STDERR: {stop_stderr.decode().strip()}"
            )
            stop_message = (f"Stop container failed!, code: {stop_proc.returncode}, "
                            f"stdout: {stop_stdout.decode()}, stderr: {stop_stderr.decode()}")
            return False, stop_message
        else:
            logging.info(
                f"[Docker] STOP succeeded.\n"
                f"STDOUT: {stop_stdout.decode().strip()}\n"
                f"STDERR: {stop_stderr.decode().strip()}"
            )
    except Exception as e:
        logging.error(f"[Docker] Exception during stop: {e}", exc_info=True)
        stop_message = f"Exception during stop container: {e}"
        return False, stop_message

    try:
        logging.info(f"[Docker] Removing container with: {remove_cmd}")
        remove_proc = await asyncio.create_subprocess_shell(
            remove_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        remove_stdout, remove_stderr = await remove_proc.communicate()

        if remove_proc.returncode != 0:
            logging.error(
                f"[Docker] REMOVE failed with return code {remove_proc.returncode}\n"
                f"STDOUT: {remove_stdout.decode().strip()}\n"
                f"STDERR: {remove_stderr.decode().strip()}"
            )
            remove_message = (f"Remove container failed!, code: {remove_proc.returncode}, "
                              f"stdout: {remove_stdout.decode()}, stderr: {remove_stderr.decode()}")
            return False, remove_message
        else:
            logging.info(
                f"[Docker] REMOVE succeeded.\n"
                f"STDOUT: {remove_stdout.decode().strip()}\n"
                f"STDERR: {remove_stderr.decode().strip()}"
            )
    except Exception as e:
        logging.error(f"[Docker] Exception during remove: {e}", exc_info=True)
        remove_message = f"Exception during remove container: {e}"
        return False, remove_message

    return True, f"Forwarder stopped and removed successfully(user_id: {user.id})"
