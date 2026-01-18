#!/usr/bin/env python3
"""
Terraform Remote State Dashboard
================================
A visual web dashboard to see your AWS resources in LocalStack or real AWS.

This dashboard displays:
- S3 Buckets (for Terraform state storage)
- DynamoDB Tables (for state locking)
- IAM Users and Access Keys
- EC2 Instances and SSH Key Pairs
- Security Groups

Usage:
    python dashboard.py              # Open dashboard (LocalStack)
    python dashboard.py --aws        # Use real AWS credentials
    python dashboard.py --no-browser # Just start server
"""

import json
import subprocess
import sys
import os
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time
import argparse

# For Windows compatibility
if sys.platform == 'win32':
    os.system('color')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

LOCALSTACK_ENDPOINT = "http://localhost:4566"
USE_AWS = False

# Colors for terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def run_aws_command(service, action, extra_args=None):
    """Run an AWS CLI command against LocalStack or real AWS."""
    cmd = ["aws"]
    if not USE_AWS:
        cmd.extend(["--endpoint-url", LOCALSTACK_ENDPOINT])
    cmd.extend([service, action, "--output", "json"])
    if extra_args:
        cmd.extend(extra_args)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return json.loads(result.stdout) if result.stdout else {}
        return None
    except Exception as e:
        return None


def get_s3_buckets():
    """Get S3 buckets."""
    data = run_aws_command("s3api", "list-buckets")
    if not data:
        return []

    buckets = []
    for bucket in data.get("Buckets", []):
        name = bucket.get("Name", "")
        # Get versioning status
        versioning = run_aws_command("s3api", "get-bucket-versioning",
                                      ["--bucket", name])
        versioning_status = versioning.get("Status", "Disabled") if versioning else "Unknown"

        buckets.append({
            "name": name,
            "created": bucket.get("CreationDate", ""),
            "versioning": versioning_status
        })
    return buckets


def get_dynamodb_tables():
    """Get DynamoDB tables."""
    data = run_aws_command("dynamodb", "list-tables")
    if not data:
        return []

    tables = []
    for table_name in data.get("TableNames", []):
        # Get table details
        details = run_aws_command("dynamodb", "describe-table",
                                  ["--table-name", table_name])
        if details and "Table" in details:
            table = details["Table"]
            hash_key = ""
            for attr in table.get("KeySchema", []):
                if attr.get("KeyType") == "HASH":
                    hash_key = attr.get("AttributeName", "")

            tables.append({
                "name": table_name,
                "hash_key": hash_key,
                "status": table.get("TableStatus", "UNKNOWN"),
                "item_count": table.get("ItemCount", 0)
            })
    return tables


def get_iam_users():
    """Get IAM users."""
    data = run_aws_command("iam", "list-users")
    if not data:
        return []

    users = []
    for user in data.get("Users", []):
        name = user.get("UserName", "")

        # Get access keys for this user
        keys_data = run_aws_command("iam", "list-access-keys",
                                    ["--user-name", name])
        access_keys = []
        if keys_data:
            for key in keys_data.get("AccessKeyMetadata", []):
                access_keys.append({
                    "id": key.get("AccessKeyId", ""),
                    "status": key.get("Status", "Unknown")
                })

        # Get attached policies
        policies_data = run_aws_command("iam", "list-attached-user-policies",
                                        ["--user-name", name])
        policies = []
        if policies_data:
            for policy in policies_data.get("AttachedPolicies", []):
                policies.append(policy.get("PolicyName", ""))

        users.append({
            "name": name,
            "arn": user.get("Arn", ""),
            "created": user.get("CreateDate", ""),
            "access_keys": access_keys,
            "policies": policies
        })
    return users


def get_key_pairs():
    """Get EC2 key pairs."""
    data = run_aws_command("ec2", "describe-key-pairs")
    if not data:
        return []

    keys = []
    for key in data.get("KeyPairs", []):
        keys.append({
            "name": key.get("KeyName", ""),
            "fingerprint": key.get("KeyFingerprint", "")[:40] + "...",
            "type": key.get("KeyType", "rsa")
        })
    return keys


def get_instances():
    """Get EC2 instances."""
    data = run_aws_command("ec2", "describe-instances")
    if not data:
        return []

    instances = []
    for reservation in data.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            name = ""
            for tag in instance.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]
                    break

            instances.append({
                "id": instance.get("InstanceId", ""),
                "name": name or "(unnamed)",
                "type": instance.get("InstanceType", ""),
                "state": instance.get("State", {}).get("Name", "unknown"),
                "public_ip": instance.get("PublicIpAddress", ""),
                "private_ip": instance.get("PrivateIpAddress", ""),
                "key_name": instance.get("KeyName", "")
            })
    return instances


def get_security_groups():
    """Get security groups (exclude default)."""
    data = run_aws_command("ec2", "describe-security-groups")
    if not data:
        return []

    sgs = []
    for sg in data.get("SecurityGroups", []):
        if sg.get("GroupName") == "default":
            continue

        ingress_rules = []
        for rule in sg.get("IpPermissions", []):
            port = rule.get("FromPort", "all")
            cidr = rule.get("IpRanges", [{}])[0].get("CidrIp", "") if rule.get("IpRanges") else ""
            ingress_rules.append(f"{port} from {cidr or 'any'}")

        sgs.append({
            "id": sg.get("GroupId", ""),
            "name": sg.get("GroupName", ""),
            "description": sg.get("Description", ""),
            "ingress_rules": ingress_rules
        })
    return sgs


def generate_html():
    """Generate the dashboard HTML."""
    s3_buckets = get_s3_buckets()
    dynamodb_tables = get_dynamodb_tables()
    iam_users = get_iam_users()
    key_pairs = get_key_pairs()
    instances = get_instances()
    security_groups = get_security_groups()

    mode = "Real AWS" if USE_AWS else "LocalStack"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terraform Remote State Dashboard - {mode}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }}

        .header {{
            text-align: center;
            padding: 30px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00d9ff, #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .header p {{ color: #888; font-size: 1.1em; }}
        .header .mode {{
            display: inline-block;
            background: {"#ff6b6b" if USE_AWS else "#00d9ff"};
            color: #1a1a2e;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-top: 10px;
        }}

        .stats {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 40px;
            flex-wrap: wrap;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px 40px;
            text-align: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .stat-card .number {{
            font-size: 3em;
            font-weight: bold;
            color: #00d9ff;
        }}
        .stat-card .label {{ color: #888; margin-top: 5px; }}

        .section {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid rgba(255,255,255,0.1);
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .section:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,217,255,0.2);
        }}
        .section h2 {{
            color: #00d9ff;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .section h2 .icon {{ font-size: 1.5em; }}

        .resource-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 15px;
        }}
        .resource-card {{
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #00d9ff;
        }}
        .resource-card.s3 {{ border-left-color: #ff6b6b; }}
        .resource-card.dynamodb {{ border-left-color: #feca57; }}
        .resource-card.iam {{ border-left-color: #45b7d1; }}
        .resource-card.keypair {{ border-left-color: #96ceb4; }}
        .resource-card.ec2 {{ border-left-color: #4ecdc4; }}
        .resource-card.sg {{ border-left-color: #ff9ff3; }}

        .resource-card h3 {{
            color: #fff;
            margin-bottom: 10px;
            font-size: 1.1em;
            word-break: break-all;
        }}
        .resource-card .id {{
            font-family: monospace;
            color: #888;
            font-size: 0.85em;
            word-break: break-all;
        }}
        .resource-card .details {{
            margin-top: 10px;
            font-size: 0.9em;
        }}
        .resource-card .details span {{
            display: inline-block;
            background: rgba(255,255,255,0.1);
            padding: 3px 8px;
            border-radius: 4px;
            margin: 2px;
        }}

        .status-running {{ color: #00ff88; }}
        .status-active {{ color: #00ff88; }}
        .status-Active {{ color: #00ff88; }}
        .status-ACTIVE {{ color: #00ff88; }}
        .status-enabled {{ color: #00ff88; }}
        .status-Enabled {{ color: #00ff88; }}

        .empty-state {{
            text-align: center;
            color: #666;
            padding: 40px;
        }}

        .architecture {{
            background: rgba(0,0,0,0.4);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 25px;
            font-family: monospace;
            white-space: pre;
            overflow-x: auto;
            line-height: 1.8;
            color: #00d9ff;
            font-size: 14px;
        }}

        .refresh-btn {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #00d9ff;
            color: #1a1a2e;
            border: none;
            padding: 15px 30px;
            border-radius: 50px;
            font-size: 1em;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,217,255,0.3);
        }}
        .refresh-btn:hover {{ background: #00ff88; }}

        /* Modal Styles */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.85);
            backdrop-filter: blur(5px);
        }}
        .modal.active {{ display: flex; align-items: center; justify-content: center; }}
        .modal-content {{
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border-radius: 16px;
            padding: 30px;
            max-width: 700px;
            max-height: 80vh;
            overflow-y: auto;
            position: relative;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            border: 1px solid rgba(0,217,255,0.2);
        }}
        .modal-close {{
            position: absolute;
            top: 15px;
            right: 20px;
            font-size: 28px;
            cursor: pointer;
            color: #888;
            transition: color 0.2s;
        }}
        .modal-close:hover {{ color: #fff; }}
        .modal-title {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #00d9ff;
        }}
        .modal-section {{
            margin-bottom: 20px;
        }}
        .modal-section h4 {{
            color: #00ff88;
            margin-bottom: 10px;
        }}
        .modal-section p {{
            line-height: 1.6;
            color: #ccc;
        }}
        .modal-section ul {{
            margin-left: 20px;
            line-height: 1.8;
            color: #ccc;
        }}
        .modal-section code {{
            background: rgba(0,217,255,0.2);
            padding: 2px 8px;
            border-radius: 4px;
            font-family: monospace;
            color: #00d9ff;
        }}
        .modal-terraform {{
            background: rgba(0,0,0,0.4);
            border-radius: 8px;
            padding: 15px;
            font-family: monospace;
            font-size: 0.85em;
            color: #feca57;
            margin-top: 10px;
            white-space: pre-wrap;
        }}
        .modal-example {{
            background: rgba(0,217,255,0.1);
            border-left: 4px solid #00d9ff;
            padding: 15px;
            border-radius: 0 8px 8px 0;
            margin-top: 15px;
        }}
        .modal-example strong {{ color: #00d9ff; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Terraform Remote State Dashboard</h1>
        <p>S3 Backend, IAM, and Compute Resources</p>
        <span class="mode">{mode}</span>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="number">{len(s3_buckets)}</div>
            <div class="label">S3 Buckets</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(dynamodb_tables)}</div>
            <div class="label">DynamoDB Tables</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(iam_users)}</div>
            <div class="label">IAM Users</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(instances)}</div>
            <div class="label">EC2 Instances</div>
        </div>
    </div>
"""

    # Architecture diagram
    if s3_buckets or dynamodb_tables or instances:
        bucket_name = s3_buckets[0]["name"][:30] if s3_buckets else "terraform-state-bucket"
        table_name = dynamodb_tables[0]["name"][:25] if dynamodb_tables else "terraform-locks"
        instance_info = f"EC2: {instances[0]['name'][:20]}" if instances else "EC2: (not created yet)"

        html += f"""
    <div class="architecture">
                    TERRAFORM REMOTE STATE ARCHITECTURE
                    ===================================

    +----------------------+          +----------------------+
    |   Your Computer      |          |   AWS / LocalStack   |
    |                      |          |                      |
    |  terraform apply ----+--------->|  S3 Bucket           |
    |                      |          |  {bucket_name:<30} |
    |  Stores state in S3  |          |  (State Storage)     |
    |                      |          +----------------------+
    |                      |                    |
    |                      |          +----------------------+
    |  Acquires lock ----->|--------->|  DynamoDB Table      |
    |                      |          |  {table_name:<25}|
    |  (Before changes)    |          |  (State Locking)     |
    |                      |          +----------------------+
    +----------------------+
                                      +----------------------+
                                      |  IAM User + Keys     |
                                      |  (Access Credentials)|
                                      +----------------------+
                                               |
                                      +--------v-------------+
                                      |  {instance_info:<20}|
                                      |  + SSH Key Pair      |
                                      |  + Security Group    |
                                      +----------------------+
    </div>
"""

    # S3 Buckets section
    html += """
    <div class="section" onclick="showModal('s3')">
        <h2><span class="icon">🪣</span> S3 Buckets (State Storage) <span style="font-size:0.5em;color:#888;margin-left:10px;">Click to learn more</span></h2>
        <div class="resource-grid">
"""
    if s3_buckets:
        for bucket in s3_buckets:
            html += f"""
            <div class="resource-card s3">
                <h3>{bucket['name']}</h3>
                <div class="details">
                    <span class="status-{bucket['versioning'].lower()}">Versioning: {bucket['versioning']}</span>
                </div>
            </div>
"""
    else:
        html += '<div class="empty-state">No S3 buckets found. Run terraform apply in the backend/ folder!</div>'

    html += """
        </div>
    </div>
"""

    # DynamoDB Tables section
    html += """
    <div class="section" onclick="showModal('dynamodb')">
        <h2><span class="icon">🗄️</span> DynamoDB Tables (State Locking) <span style="font-size:0.5em;color:#888;margin-left:10px;">Click to learn more</span></h2>
        <div class="resource-grid">
"""
    if dynamodb_tables:
        for table in dynamodb_tables:
            html += f"""
            <div class="resource-card dynamodb">
                <h3>{table['name']}</h3>
                <div class="details">
                    <span>Hash Key: {table['hash_key']}</span>
                    <span class="status-{table['status'].lower()}">{table['status']}</span>
                </div>
            </div>
"""
    else:
        html += '<div class="empty-state">No DynamoDB tables found. Run terraform apply in the backend/ folder!</div>'

    html += """
        </div>
    </div>
"""

    # IAM Users section
    html += """
    <div class="section" onclick="showModal('iam')">
        <h2><span class="icon">👤</span> IAM Users & Access Keys <span style="font-size:0.5em;color:#888;margin-left:10px;">Click to learn more</span></h2>
        <div class="resource-grid">
"""
    if iam_users:
        for user in iam_users:
            keys_html = ""
            for key in user['access_keys']:
                keys_html += f"<span class='status-{key['status'].lower()}'>{key['id'][:16]}...</span> "

            policies_html = ", ".join(user['policies'][:3]) if user['policies'] else "None"

            html += f"""
            <div class="resource-card iam">
                <h3>{user['name']}</h3>
                <div class="id">{user['arn']}</div>
                <div class="details">
                    <div>Access Keys: {keys_html or 'None'}</div>
                    <div>Policies: {policies_html}</div>
                </div>
            </div>
"""
    else:
        html += '<div class="empty-state">No IAM users found. Run terraform apply in the iam/ folder!</div>'

    html += """
        </div>
    </div>
"""

    # Key Pairs section
    html += """
    <div class="section" onclick="showModal('keypair')">
        <h2><span class="icon">🔑</span> SSH Key Pairs <span style="font-size:0.5em;color:#888;margin-left:10px;">Click to learn more</span></h2>
        <div class="resource-grid">
"""
    if key_pairs:
        for key in key_pairs:
            html += f"""
            <div class="resource-card keypair">
                <h3>{key['name']}</h3>
                <div class="id">{key['fingerprint']}</div>
                <div class="details">
                    <span>Type: {key['type']}</span>
                </div>
            </div>
"""
    else:
        html += '<div class="empty-state">No SSH key pairs found. Run terraform apply in the compute/ folder!</div>'

    html += """
        </div>
    </div>
"""

    # EC2 Instances section
    html += """
    <div class="section" onclick="showModal('ec2')">
        <h2><span class="icon">💻</span> EC2 Instances <span style="font-size:0.5em;color:#888;margin-left:10px;">Click to learn more</span></h2>
        <div class="resource-grid">
"""
    if instances:
        for instance in instances:
            html += f"""
            <div class="resource-card ec2">
                <h3>{instance['name']}</h3>
                <div class="id">{instance['id']}</div>
                <div class="details">
                    <span>{instance['type']}</span>
                    <span class="status-{instance['state']}">{instance['state']}</span>
                    <span>IP: {instance['public_ip'] or instance['private_ip'] or 'N/A'}</span>
                    <span>Key: {instance['key_name']}</span>
                </div>
            </div>
"""
    else:
        html += '<div class="empty-state">No EC2 instances found. Run terraform apply in the compute/ folder!</div>'

    html += """
        </div>
    </div>
"""

    # Security Groups section
    html += """
    <div class="section" onclick="showModal('sg')">
        <h2><span class="icon">🔒</span> Security Groups <span style="font-size:0.5em;color:#888;margin-left:10px;">Click to learn more</span></h2>
        <div class="resource-grid">
"""
    if security_groups:
        for sg in security_groups:
            rules_html = "<br>".join(sg['ingress_rules'][:3]) if sg['ingress_rules'] else "No inbound rules"
            html += f"""
            <div class="resource-card sg">
                <h3>{sg['name']}</h3>
                <div class="id">{sg['id']}</div>
                <div class="details">
                    <div>{rules_html}</div>
                </div>
            </div>
"""
    else:
        html += '<div class="empty-state">No security groups found (besides default)</div>'

    html += """
        </div>
    </div>

    <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>

    <!-- Modal Container -->
    <div id="modal" class="modal" onclick="if(event.target===this)closeModal()">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal()">&times;</span>
            <div id="modal-body"></div>
        </div>
    </div>

    <script>
        const explanations = {
            s3: {
                title: '🪣 S3 Backend for Terraform State',
                content: `
                    <div class="modal-section">
                        <h4>What is Terraform State?</h4>
                        <p>Terraform keeps track of all resources it manages in a "state file". This file maps your configuration to real-world resources and stores metadata like resource IDs.</p>
                    </div>
                    <div class="modal-section">
                        <h4>Why Store State in S3?</h4>
                        <ul>
                            <li><strong>Team Collaboration</strong> - Everyone uses the same state</li>
                            <li><strong>Durability</strong> - S3 has 99.999999999% durability</li>
                            <li><strong>Versioning</strong> - Roll back to previous states</li>
                            <li><strong>Encryption</strong> - Protect sensitive data</li>
                        </ul>
                    </div>
                    <div class="modal-section">
                        <h4>Terraform Example</h4>
                        <div class="modal-terraform">terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "project/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}</div>
                    </div>
                    <div class="modal-example">
                        <strong>Important:</strong> Always enable versioning and encryption on your state bucket. State files often contain sensitive data like passwords and API keys.
                    </div>
                `
            },
            dynamodb: {
                title: '🗄️ DynamoDB for State Locking',
                content: `
                    <div class="modal-section">
                        <h4>Why State Locking?</h4>
                        <p>Without locking, two people running terraform apply at the same time could corrupt the state file. DynamoDB provides distributed locking to prevent this.</p>
                    </div>
                    <div class="modal-section">
                        <h4>How It Works</h4>
                        <ul>
                            <li>Before any write operation, Terraform acquires a lock</li>
                            <li>The lock is stored as an item in DynamoDB</li>
                            <li>Other operations wait until the lock is released</li>
                            <li>Lock is automatically released after operation completes</li>
                        </ul>
                    </div>
                    <div class="modal-section">
                        <h4>Terraform Example</h4>
                        <div class="modal-terraform">resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"  # Must be exactly "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}</div>
                    </div>
                    <div class="modal-example">
                        <strong>Critical:</strong> The hash key MUST be named exactly "LockID" (case-sensitive). Terraform expects this specific name.
                    </div>
                `
            },
            iam: {
                title: '👤 IAM Users & Access Keys',
                content: `
                    <div class="modal-section">
                        <h4>What are IAM Users?</h4>
                        <p>IAM Users are identities in AWS that can authenticate and be authorized to use AWS services. Each user has credentials (password or access keys) to access AWS.</p>
                    </div>
                    <div class="modal-section">
                        <h4>Access Keys</h4>
                        <ul>
                            <li><strong>Access Key ID</strong> - Like a username (safe to share)</li>
                            <li><strong>Secret Access Key</strong> - Like a password (KEEP SECRET!)</li>
                            <li>Used for programmatic access (CLI, SDK, Terraform)</li>
                            <li>Can be rotated without changing the user</li>
                        </ul>
                    </div>
                    <div class="modal-section">
                        <h4>Terraform Example</h4>
                        <div class="modal-terraform">resource "aws_iam_user" "terraform" {
  name = "terraform-user"
}

resource "aws_iam_access_key" "terraform" {
  user = aws_iam_user.terraform.name
}

output "secret_access_key" {
  value     = aws_iam_access_key.terraform.secret
  sensitive = true  # Don't show in logs!
}</div>
                    </div>
                    <div class="modal-example">
                        <strong>Security Best Practice:</strong> Never commit access keys to git! Use environment variables or AWS profiles. Rotate keys regularly.
                    </div>
                `
            },
            keypair: {
                title: '🔑 SSH Key Pairs',
                content: `
                    <div class="modal-section">
                        <h4>What are SSH Key Pairs?</h4>
                        <p>SSH key pairs provide secure access to EC2 instances. They use public-key cryptography: AWS stores the public key, you keep the private key.</p>
                    </div>
                    <div class="modal-section">
                        <h4>How They Work</h4>
                        <ul>
                            <li><strong>Public Key</strong> - Stored on the EC2 instance</li>
                            <li><strong>Private Key</strong> - Stored on your computer (.pem file)</li>
                            <li>Only the private key holder can log in</li>
                            <li>Much more secure than passwords</li>
                        </ul>
                    </div>
                    <div class="modal-section">
                        <h4>Terraform Example</h4>
                        <div class="modal-terraform">resource "tls_private_key" "ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "deployer" {
  key_name   = "my-key"
  public_key = tls_private_key.ssh.public_key_openssh
}

resource "local_file" "private_key" {
  content         = tls_private_key.ssh.private_key_pem
  filename        = "private-key.pem"
  file_permission = "0400"
}</div>
                    </div>
                    <div class="modal-example">
                        <strong>Usage:</strong> <code>ssh -i private-key.pem ec2-user@IP_ADDRESS</code>
                    </div>
                `
            },
            ec2: {
                title: '💻 EC2 Instances',
                content: `
                    <div class="modal-section">
                        <h4>What is EC2?</h4>
                        <p>EC2 (Elastic Compute Cloud) provides virtual servers in the cloud. You can launch instances, install software, and run applications - like physical servers but on-demand.</p>
                    </div>
                    <div class="modal-section">
                        <h4>Key Components</h4>
                        <ul>
                            <li><strong>AMI</strong> - The operating system image</li>
                            <li><strong>Instance Type</strong> - CPU, memory, network (t2.micro is free tier)</li>
                            <li><strong>Key Pair</strong> - SSH access credentials</li>
                            <li><strong>Security Group</strong> - Firewall rules</li>
                        </ul>
                    </div>
                    <div class="modal-section">
                        <h4>Terraform Example</h4>
                        <div class="modal-terraform">data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t2.micro"
  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.ssh.id]
}</div>
                    </div>
                `
            },
            sg: {
                title: '🔒 Security Groups',
                content: `
                    <div class="modal-section">
                        <h4>What is a Security Group?</h4>
                        <p>A Security Group acts as a virtual firewall for your EC2 instances. It controls inbound and outbound traffic at the instance level.</p>
                    </div>
                    <div class="modal-section">
                        <h4>Key Rules</h4>
                        <ul>
                            <li><strong>Default DENY</strong> - All inbound traffic blocked by default</li>
                            <li><strong>Stateful</strong> - Return traffic automatically allowed</li>
                            <li><strong>Port 22</strong> - SSH access</li>
                            <li><strong>0.0.0.0/0</strong> - Open to all IPs (use with caution!)</li>
                        </ul>
                    </div>
                    <div class="modal-section">
                        <h4>Terraform Example</h4>
                        <div class="modal-terraform">resource "aws_security_group" "ssh" {
  name        = "allow-ssh"
  description = "Allow SSH inbound"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["YOUR_IP/32"]  # Restrict to your IP!
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}</div>
                    </div>
                    <div class="modal-example">
                        <strong>Security Best Practice:</strong> Never open port 22 to 0.0.0.0/0 in production. Always restrict SSH access to specific IP addresses.
                    </div>
                `
            }
        };

        function showModal(type) {
            const modal = document.getElementById('modal');
            const body = document.getElementById('modal-body');
            const data = explanations[type];
            if (data) {
                body.innerHTML = '<div class="modal-title">' + data.title + '</div>' + data.content;
                modal.classList.add('active');
            }
        }

        function closeModal() {
            document.getElementById('modal').classList.remove('active');
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeModal();
        });
    </script>
</body>
</html>
"""
    return html


def check_localstack():
    """Check if LocalStack is running."""
    try:
        result = subprocess.run(
            ["curl", "-s", f"{LOCALSTACK_ENDPOINT}/_localstack/health"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except:
        return False


def check_aws_credentials():
    """Check if AWS credentials are configured."""
    try:
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except:
        return False


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = generate_html()
            self.wfile.write(html.encode())
        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass  # Suppress logging


def main():
    global USE_AWS

    parser = argparse.ArgumentParser(description="Terraform Remote State Dashboard")
    parser.add_argument("--aws", action="store_true", help="Use real AWS instead of LocalStack")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    args = parser.parse_args()

    USE_AWS = args.aws

    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  Terraform Remote State Dashboard{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")

    if USE_AWS:
        print(f"  Mode: {Colors.YELLOW}Real AWS{Colors.END}")
        print(f"  Checking AWS credentials... ", end="")
        if not check_aws_credentials():
            print(f"{Colors.RED}NOT CONFIGURED{Colors.END}")
            print(f"\n  {Colors.YELLOW}Configure AWS credentials first:{Colors.END}")
            print(f"  aws configure")
            print(f"  # Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY\n")
            sys.exit(1)
        print(f"{Colors.GREEN}OK{Colors.END}")
    else:
        print(f"  Mode: {Colors.CYAN}LocalStack{Colors.END}")
        print(f"  Checking LocalStack... ", end="")
        if not check_localstack():
            print(f"{Colors.RED}NOT RUNNING{Colors.END}")
            print(f"\n  {Colors.YELLOW}Start LocalStack first:{Colors.END}")
            print(f"  docker-compose up -d\n")
            sys.exit(1)
        print(f"{Colors.GREEN}OK{Colors.END}")

    # Start server
    port = 8080
    server = HTTPServer(("localhost", port), DashboardHandler)

    print(f"\n  {Colors.GREEN}Dashboard running at:{Colors.END}")
    print(f"  {Colors.BOLD}http://localhost:{port}{Colors.END}\n")
    print(f"  Press Ctrl+C to stop.\n")

    # Open browser
    if not args.no_browser:
        def open_browser():
            time.sleep(1)
            webbrowser.open(f"http://localhost:{port}")
        threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n\n  {Colors.YELLOW}Dashboard stopped.{Colors.END}\n")
        server.shutdown()


if __name__ == "__main__":
    main()
