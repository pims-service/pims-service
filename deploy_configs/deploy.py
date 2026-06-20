import os
import sys
import zipfile
import paramiko

# ==============================================================================
# Configuration Parameters (Hostinger KVM 2 Server Details)
# ==============================================================================
VM_HOST = "your-hostinger-kvm2-ip-here"
VM_PORT = 22
VM_USER = "root"                         # Hostinger KVM default user is root
VM_PASSWORD = "your-root-password-here"  # Or configure SSH keys below
VM_KEY_PATH = None                       # Path to private SSH key file (optional)
REMOTE_DIR = "/root/psych_experiment_platform"


# File name for temporary archive
ARCHIVE_NAME = "project_deployment.zip"

def create_zip_archive(source_dir, output_path):
    """Creates a zip archive of the workspace, excluding local configs, git, and build outputs."""
    print("=== Packaging local codebase ===")
    
    # Files/directories to exclude from packaging
    exclude_dirs = {
        '.git', 
        'venv', 
        '.venv', 
        'node_modules', 
        '__pycache__', 
        '.pytest_cache', 
        'dist', 
        'build', 
        'deploy_configs',  # Don't upload deployment credentials folder
        'scratch',
    }
    exclude_files = {
        ARCHIVE_NAME,
        '.env',
        'db.sqlite3',
        'celerybeat-schedule',
        'django.log',
    }

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Modify dirs in-place to avoid traversing excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file in exclude_files or file.endswith('.log'):
                    continue
                
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_dir)
                zipf.write(full_path, rel_path)
                
    print(f"Codebase packaged successfully: {output_path} ({os.path.getsize(output_path) / (1024*1024):.2f} MB)")

def run_ssh_command(ssh, cmd):
    """Helper to execute an SSH command and print stdout/stderr."""
    print(f"\nExecuting: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    
    if out.strip():
        print("STDOUT:")
        print(out.strip())
    if err.strip():
        print("STDERR:")
        print(err.strip())
        
    exit_status = stdout.channel.recv_exit_status()
    print(f"Command exited with status code: {exit_status}")
    return exit_status == 0

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    archive_path = os.path.join(project_root, ARCHIVE_NAME)
    env_source_path = os.path.join(script_dir, "env.production")

    # 1. Package codebase
    create_zip_archive(project_root, archive_path)

    # 2. Check env file
    if not os.path.exists(env_source_path):
        print(f"ERROR: Local production environment config '{env_source_path}' not found!")
        print("Please copy 'env.template' to 'env.production' and fill in variables first.")
        if os.path.exists(archive_path):
            os.remove(archive_path)
        sys.exit(1)

    # 3. Connect to SSH
    print("\n=== Connecting to target server via SSH ===")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        connect_params = {
            "hostname": VM_HOST,
            "port": VM_PORT,
            "username": VM_USER,
            "timeout": 15
        }
        if VM_KEY_PATH:
            connect_params["key_filename"] = VM_KEY_PATH
        elif VM_PASSWORD:
            connect_params["password"] = VM_PASSWORD
            
        ssh.connect(**connect_params)
        print(f"Connected to {VM_HOST} successfully!")
    except Exception as e:
        print(f"Connection failed: {e}")
        if os.path.exists(archive_path):
            os.remove(archive_path)
        sys.exit(1)

    try:
        sftp = ssh.open_sftp()
        
        # 4. Prepare Remote Directory
        print(f"\n=== Preparing remote deployment folder: {REMOTE_DIR} ===")
        run_ssh_command(ssh, f"mkdir -p {REMOTE_DIR}")

        # 5. Upload Code Archive
        remote_zip_path = f"{REMOTE_DIR}/{ARCHIVE_NAME}"
        print(f"\n=== Uploading code archive to {remote_zip_path} ===")
        sftp.put(archive_path, remote_zip_path)
        print("Upload completed.")

        # 6. Upload Environment Config
        print("\n=== Uploading Environment Configuration ===")
        # Root level .env
        sftp.put(env_source_path, f"{REMOTE_DIR}/.env")
        # Backend directory .env
        run_ssh_command(ssh, f"mkdir -p {REMOTE_DIR}/backend")
        sftp.put(env_source_path, f"{REMOTE_DIR}/backend/.env")
        print(".env configuration deployed.")

        sftp.close()

        # 7. Unpack Codebase on server
        print("\n=== Unpacking codebase on remote server ===")
        unpack_cmd = f"cd {REMOTE_DIR} && unzip -o {ARCHIVE_NAME} && rm {ARCHIVE_NAME}"
        run_ssh_command(ssh, unpack_cmd)

        # 8. Start/Rebuild Containers
        print("\n=== Building and starting Docker containers ===")
        docker_cmd = f"cd {REMOTE_DIR} && docker compose down && docker compose up -d --build"
        run_ssh_command(ssh, docker_cmd)

        # 9. Run Database Migrations
        print("\n=== Running Database Migrations ===")
        migrate_cmd = f"cd {REMOTE_DIR} && docker compose exec -T backend python manage.py migrate"
        run_ssh_command(ssh, migrate_cmd)

        # 10. Seed Core Activities / Questions
        print("\n=== Seeding Core Activities and Scales ===")
        # Seed Scales
        seed_scales_cmd = f"cd {REMOTE_DIR} && docker compose exec -T backend python manage.py seed_longitudinal_scales"
        run_ssh_command(ssh, seed_scales_cmd)
        # Seed Daily Reflection prompts
        seed_activities_cmd = f"cd {REMOTE_DIR} && docker compose exec -T backend python manage.py seed_daily_tasks"
        run_ssh_command(ssh, seed_activities_cmd)

        # 11. Backfill PERMA baseline reports for pre-feature T0 completions
        print("\n=== Dispatching missing PERMA baseline reports (pre-feature T0 users) ===")
        backfill_cmd = f"cd {REMOTE_DIR} && docker compose exec -T backend python manage.py send_missing_signup_reports"
        run_ssh_command(ssh, backfill_cmd)

        print("\n=== DEPLOYMENT COMPLETED SUCCESSFULY ===")
        print(f"Service running at: http://{VM_HOST}:{4756}")
        
    finally:
        ssh.close()
        # Clean up local zip
        if os.path.exists(archive_path):
            os.remove(archive_path)

if __name__ == "__main__":
    main()
