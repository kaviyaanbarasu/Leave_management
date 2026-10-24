import subprocess

PASSWORD = "admin12345"

def find_user(db, name):
    db.execute(f"SELECT * FROM users WHERE name = '{name}'")

def run(cmd):
    return subprocess.run(cmd, shell=True)
