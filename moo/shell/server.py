import asyncio
import logging

from django.contrib.auth.models import User  # pylint: disable=imported-auth-user

from simplesshkey.models import UserKey
import asyncssh
from asgiref.sync import sync_to_async
from prompt_toolkit.contrib.ssh import PromptToolkitSSHServer, PromptToolkitSSHSession

from .prompt import embed

log = logging.getLogger(__name__)

async def interact(ssh_session: PromptToolkitSSHSession) -> None:
    await embed(ssh_session.user)
    log.info(f"{ssh_session.user} disconnected.")

async def server(port=8022):
    await asyncio.sleep(1)
    await asyncssh.create_server(
        lambda: SSHServer(interact),
        "",
        port,
        server_host_keys=["/etc/ssh/ssh_host_ecdsa_key"],
    )
    await asyncio.Future()

class SSHServer(PromptToolkitSSHServer):
    def begin_auth(self, _: str) -> bool:
        return True

    def password_auth_supported(self) -> bool:
        return True

    @sync_to_async
    def validate_password(self, username: str, password: str) -> bool:
        user = User.objects.get(username=username)
        if user.check_password(password):
            self.user = user  # pylint: disable=attribute-defined-outside-init
            return True
        return False

    def public_key_auth_supported(self) -> bool:
        return True

    @sync_to_async
    def validate_public_key(self, username: str, key: asyncssh.SSHKey):
        for user_key in UserKey.objects.filter(user__username=username):
            user_pem = ' '.join(user_key.key.split()[:2]) + "\n"
            server_pem = key.export_public_key().decode('utf8')
            if user_pem == server_pem:
                self.user = user_key.user  # pylint: disable=attribute-defined-outside-init
                return True
        return False

    def session_requested(self) -> PromptToolkitSSHSession:
        session = PromptToolkitSSHSession(self.interact, enable_cpr=self.enable_cpr)
        session.user = self.user
        return session
