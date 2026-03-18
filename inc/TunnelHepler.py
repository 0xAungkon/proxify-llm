import subprocess
import threading
import re
import time
from inc.LogHelpers import logger
from config.settings import settings


class PinggyHelper:
    def __init__(self, config):
        self.config = config
        self.process = None
        self.tunnel_url = None
        self.tunnel_thread = None

    def start_tunnel(self, local_port, tunnel_token=None):
        """
        Start Pinggy SSH tunnel in background.
        
        Args:
            local_port: Local FastAPI port to forward (default 8000)
            tunnel_token: Optional custom tunnel token (user@host format)
                         If not provided, uses qr@free.pinggy.io
        """
        # Determine SSH host
        ssh_host = tunnel_token if tunnel_token else "qr@free.pinggy.io"
        
        # SSH command to open tunnel
        ssh_command = [
            "ssh",
            "-p", "443",
            "-R0:localhost:{}".format(local_port),
            "-t",
            ssh_host,
            "u:Host:localhost:{}".format(local_port)
        ]
        
        logger.info(f"Starting Pinggy tunnel on port {local_port}")
        logger.info(f"SSH host: {ssh_host}")
        logger.info(f"Command: {' '.join(ssh_command)}")
        
        # Start tunnel in background thread
        self.tunnel_thread = threading.Thread(
            target=self._run_tunnel,
            args=(ssh_command,),
            daemon=True
        )
        self.tunnel_thread.start()
        
        # Give tunnel time to establish and extract URL
        time.sleep(3)
        
        if self.tunnel_url:
            logger.info(f"✓ Tunnel established! Public URL: {self.tunnel_url}")
            print(f"\n{'='*60}")
            print(f"🌐 Tunnel URL: {self.tunnel_url}")
            print(f"{'='*60}\n")
        else:
            logger.warning("Tunnel started but URL not yet available")

    def _run_tunnel(self, ssh_command):
        """
        Run SSH tunnel and capture output for URL extraction.
        """
        try:
            # Create process with stdin for password
            self.process = subprocess.Popen(
                ssh_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Send password if prompted
            time.sleep(0.5)
            password = settings.admin_password if settings.admin_password else "7530"
            self.process.stdin.write(f"{password}\n")
            self.process.stdin.flush()
            
            # Read output and extract tunnel URL
            for line in self.process.stdout:
                line = line.strip()
                if line:
                    logger.debug(f"[Pinggy] {line}")
                    
                    # Extract tunnel URL from output
                    # Pinggy outputs URLs like: https://xyz-abc.free.pinggy.link or http://xyz-abc.free.pinggy.link
                    url_match = re.search(r'https?://[^\s]+\.free\.pinggy\.link[^\s]*', line)
                    if url_match:
                        self.tunnel_url = url_match.group(0)
                        logger.info(f"Tunnel URL detected: {self.tunnel_url}")
                        print(f"\n{'='*60}")
                        print(f"🌐 Tunnel URL: {self.tunnel_url}")
                        print(f"{'='*60}\n")
                        
        except Exception as e:
            logger.error(f"Tunnel error: {e}")
            print(f"❌ Tunnel error: {e}")

    def stop_tunnel(self):
        """Stop the SSH tunnel."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                logger.info("Tunnel stopped")
            except subprocess.TimeoutExpired:
                self.process.kill()
                logger.info("Tunnel forcefully terminated")

    def get_tunnel_info(self):
        """Get current tunnel information."""
        return {
            "tunnel_url": self.tunnel_url,
            "status": "active" if self.process and self.process.poll() is None else "inactive",
            "ssh_host": self.config
        }


