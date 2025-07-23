import subprocess
from utils.logger import setup_logger

logger = setup_logger()

def run_ansible_playbook():
    """Run an Ansible playbook to configure instances."""
    playbook_path = "playbooks/configure_instance.yml"
    logger.info(f"Running Ansible playbook: {playbook_path}")
    try:
        subprocess.run([
            "ansible-playbook", playbook_path,
            "--inventory", "localhost,"
        ], check=True)
        logger.info("Ansible playbook executed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run Ansible playbook: {e}")